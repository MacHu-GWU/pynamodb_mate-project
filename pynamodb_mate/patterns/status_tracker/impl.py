# -*- coding: utf-8 -*-

"""
Implements the DynamoDB status tracking pattern.
"""

import typing as T
import enum
import uuid
import inspect
import traceback
import dataclasses
from contextlib import contextmanager

from datetime import datetime, timezone

from iterproxy import IterProxy
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
    JSONAttribute,
)
from pynamodb.indexes import (
    GlobalSecondaryIndex,
    AllProjection,
)
from pynamodb.settings import OperationSettings

from ...models import Model
from ...compat import cached_property


class BaseStatusEnum(int, enum.Enum):
    """
    Base enum class to define the status code you want the tracker to track.

    The value of the status should be an integer. For example, you have a task
    that has the following status:

    .. code-block:: python

        class StatusEnum(BaseStatusEnum):
            s00_todo = 0 # the task is defined but not started
            s03_in_progress = 3 # the task is in progress
            s06_failed = 6 # the task failed
            s09_success = 9 # the task succeeded
            s10_ignore = 10 # the task already failed multiple times, it is ignored

    """

    @property
    def status_name(self) -> str:
        """
        Human readable status name.
        """
        return self.name

    @classmethod
    def from_value(cls, value: int) -> "BaseStatusEnum":
        """
        Get status enum object from it's value.
        """
        return cls(value)

    @classmethod
    def value_to_name(cls, value: int) -> str:
        """
        Convert status value to status name.
        """
        return cls.from_value(value).name

    @classmethod
    def values(cls) -> T.List[int]:
        """
        Return list of all available status values.
        """
        return [status.value for status in cls]


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def utc_now() -> datetime:
    """
    Get time aware utc now datetime object.
    """
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class StatusAndCreateTimeIndex(GlobalSecondaryIndex):
    """
    GSI for query by job_id and status.

    .. versionchanged:: 5.3.4.7

        1. ``StatusAndTaskIdIndex`` is renamed to ``StatusAndCreateTimeIndex``
        2. it now uses ``create_time`` as the range key.
        3. it now uses AllProjection
    """

    class Meta:
        index_name = "status_and_create_time-index"
        projection = AllProjection()

    value: T.Union[str, UnicodeAttribute] = UnicodeAttribute(hash_key=True)
    create_time: T.Union[datetime, UTCDateTimeAttribute] = UTCDateTimeAttribute(
        range_key=True
    )


class TaskLockedError(Exception):
    """
    Raised when a task worker is trying to work on a locked task.
    """

    pass


class TaskIgnoredError(Exception):
    """
    Raised when a task is already in "ignore" status (You need to define).
    """

    pass


# update context manager in-memory cache
_update_context: T.Dict[
    str,  # the Dynamodb item hash key
    T.Dict[
        str,  # item attribute name
        T.Dict[
            str,  # there are three key, "old" (value), "new" (value), "act" (update action)
            T.Any,
        ],
    ],
] = dict()


@dataclasses.dataclass
class BaseDataClass:
    """
    Base dataclass for data and errors.
    """

    @classmethod
    def from_dict(cls, dct: dict):
        return cls(**dct)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class BaseData(BaseDataClass):
    """
    Base dataclass for data attribute, if you want to use a class instead of
    dict to manage the data attribute. You can inherit from this class and
    define your own data fields.
    """

    pass


@dataclasses.dataclass
class BaseErrors(BaseDataClass):
    error: T.Optional[str] = dataclasses.field(default=None)
    traceback: T.Optional[str] = dataclasses.field(default=None)


class BaseStatusTracker(Model):
    """
    The DynamoDB ORM model for the status tracking. You can use one
    DynamoDB table for multiple status tracking jobs.

    Concepts:

    - job: a high-level description of a job, the similar task on different
        items will be grouped into one job. ``job_id`` is the unique identifier
        for a job.
    - task: a specific task on a specific item. ``task_id`` is the unique identifier
        for a task. Within the same job, ``task_id`` has to be unique. But it can
        be duplicated across different jobs.
    - status: an integer value to indicate the status of a task. The closer to
        the end, the value should be larger, so we can compare the values.

    Attributes:

    :param key: The unique identifier of the task. It is a compound key of
        job_id and task_id. The format is ``{job_id}{separator}{task_id}``
    :param value: Indicate the status of the task. The format is
        ``{job_id}{separator}{status_code}``.
    :param update_time: when the task status is updated
    :param retry: how many times the task has been retried
    :param lock: a concurrency control mechanism. It is an uuid string.
    :param lock_time: when this task is locked.
    :param data: arbitrary data in python dictionary.
    :param errors: arbitrary error data in python dictionary.


    .. versionchanged:: 5.3.4.7

        1. added ``create_time`` attribute.
    """

    key: T.Union[str, UnicodeAttribute] = UnicodeAttribute(hash_key=True)
    value: T.Union[str, UnicodeAttribute] = UnicodeAttribute()
    create_time: T.Union[datetime, UTCDateTimeAttribute] = UTCDateTimeAttribute(
        default=utc_now,
    )
    update_time: T.Union[datetime, UTCDateTimeAttribute] = UTCDateTimeAttribute(
        default=utc_now,
    )
    retry: T.Union[int, NumberAttribute] = NumberAttribute(default=0)
    lock: T.Union[T.Optional[str], UnicodeAttribute] = UnicodeAttribute(
        default=None,
        null=True,
    )
    lock_time: T.Union[datetime, UTCDateTimeAttribute] = UTCDateTimeAttribute(
        default=EPOCH,
    )
    data: T.Optional[T.Union[dict, JSONAttribute]] = JSONAttribute(
        default=lambda: dict(),
        null=True,
    )
    errors: T.Optional[T.Union[dict, JSONAttribute]] = JSONAttribute(
        default=lambda: dict(),
        null=True,
    )

    _status_and_create_time_index: T.Optional[StatusAndCreateTimeIndex] = None

    # one DynamoDB table can serve multiple jobs
    # if you defined a default job id for the table
    # you don't need to explicitly specify the job id in many API
    JOB_ID: T.Optional[str] = None
    # the separator string between job_id and task_id
    SEP = "____"
    # how many digits the max status code have, this ensures that the
    # status can be used in comparison
    STATUS_ZERO_PAD: int = 3
    # how many retry is allowed before we ignore it
    MAX_RETRY: int = 3
    # how long the lock will expire
    LOCK_EXPIRE_SECONDS: int = 900
    # the default status code, means "to do", usually start from 0
    DEFAULT_STATUS: int = 0
    # the status enum class for this tracker
    STATUS_ENUM: T.Optional[T.Type[BaseStatusEnum]] = None

    @classmethod
    def make_key(
        cls,
        task_id: str,
        job_id: T.Optional[str] = None,
    ) -> str:
        """
        Join the job_id and task_id to create the DynamoDB hash key.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        return f"{JOB_ID}{cls.SEP}{task_id}"

    @classmethod
    def make_value(
        cls,
        status: int,
        job_id: T.Optional[str] = None,
    ) -> str:
        """
        Join the job_id and status to create the ``value`` attribute.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        return f"{JOB_ID}{cls.SEP}{str(status).zfill(cls.STATUS_ZERO_PAD)}"

    @cached_property
    def job_id(self) -> str:
        return self.key.split(self.SEP)[0]

    @cached_property
    def task_id(self) -> str:
        """
        Return the task_id part of the key. It should be unique with in a job.
        """
        return self.key.split(self.SEP)[1]

    @property
    def status(self) -> int:
        """
        Return the status value of the task.
        """
        return int(self.value.split(self.SEP)[1])

    @property
    def status_name(self) -> str:
        """
        Return the status name of the task. If you don't set the Status enum
        class to the ``STATUS_ENUM`` class attribute, it returns the integer
        value of the status. If you did so, it returns the human-friendly
        status name.
        """
        if self.STATUS_ENUM is None:
            return str(self.status)
        else:
            return self.STATUS_ENUM.value_to_name(self.status)

    @classmethod
    def get_one_or_none(
        cls,
        task_id: str,
        consistent_read: bool = False,
        attributes_to_get: T.Optional[T.Sequence[str]] = None,
        settings: OperationSettings = OperationSettings.default,
        job_id: T.Optional[str] = None,
    ) -> T.Optional["BaseStatusTracker"]:
        """
        Get one item by task_id. If the item does not exist, return None.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        return super().get_one_or_none(
            hash_key=cls.make_key(task_id, JOB_ID),
            consistent_read=consistent_read,
            attributes_to_get=attributes_to_get,
            settings=settings,
        )

    def is_item_exists(self) -> bool:
        """
        Check if this Dynamodb item exists.
        """
        return (
            self.get_one_or_none(
                task_id=self.task_id,
                attributes_to_get=[
                    "key",
                ],
            )
            is not None
        )

    @classmethod
    def make(
        cls,
        task_id: str,
        status: int,
        data: T.Optional[dict] = None,
        job_id: T.Optional[str] = None,
    ) -> "BaseStatusTracker":
        """
        A factory method to create new instance of a tracker.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        kwargs = dict(
            key=cls.make_key(task_id, JOB_ID),
            value=cls.make_value(status),
        )
        if data is not None:
            kwargs["data"] = data
        return cls(**kwargs)

    @classmethod
    def new(
        cls,
        task_id: str,
        data: T.Optional[dict] = None,
        save: bool = True,
        job_id: T.Optional[str] = None,
    ) -> "BaseStatusTracker":
        """
        A factory method to create new task with the default status (usually 0).

        :param save: if True, also save the item to dynamodb.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        obj = cls.make(
            task_id=task_id,
            status=cls.DEFAULT_STATUS,
            data=data,
            job_id=JOB_ID,
        )
        if save:
            obj.save()
        return obj

    @classmethod
    def delete_all_by_job_id(
        cls,
        job_id: T.Optional[str] = None,
    ) -> int:
        """
        Delete all item belongs to specific job.

        Note: this method is expensive, it will scan a lot of items.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        ith = 0
        with cls.batch_write() as batch:
            for ith, item in enumerate(
                cls.scan(
                    filter_condition=cls.key.startswith(JOB_ID),
                    attributes_to_get=[
                        "key",
                    ],
                ),
                start=1,
            ):
                batch.delete(item)
        return ith

    @classmethod
    def count_items_by_job_id(
        cls,
        job_id: T.Optional[str] = None,
    ):
        """
        Count number of items belong to specific job.

        Note: this method is expensive, it will scan a lot of items.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        ith = 0
        for ith, item in enumerate(
            cls.scan(
                filter_condition=cls.key.startswith(JOB_ID),
                attributes_to_get=[
                    "key",
                ],
            ),
            start=1,
        ):
            pass
        return ith

    def is_locked(self) -> bool:
        """
        Check if the task is locked.
        """
        if self.lock is None:
            return False
        else:
            now = utc_now()
            return (now - self.lock_time).total_seconds() < self.LOCK_EXPIRE_SECONDS

    def _setup_update_context(self):
        _update_context[self.key] = dict()

    def _rollback_update_context(self):
        for attr_name, dct in _update_context[self.key].items():
            setattr(self, attr_name, dct["old"])

    def _flush_update_context(self):
        actions = [dct["act"] for dct in _update_context[self.key].values()]
        if len(actions):
            # print("flushing update data to Dyanmodb")
            # print(f"actions: {actions}")
            # pynamodb update API will apply the updated data to the current
            # item object.
            self.update(actions=actions)

    def _teardown_update_context(self):
        del _update_context[self.key]

    @contextmanager
    def update_context(self) -> "BaseStatusTracker":
        """
        A context manager to update the attributes of the task.
        If the update fails, the attributes will be rolled back to the original
        value.

        Usage::

            tracker = Tracker.new(job_id="my-job", task_id="task-1")
            with tracker.update_context():
                tracker.set_status(StatusEnum.s03_in_progress)
                tracker.set_data({"foo": "bar"})
        """
        try:
            self._setup_update_context()
            yield self
            self._flush_update_context()
        except Exception as e:
            self._rollback_update_context()
            raise e
        finally:
            self._teardown_update_context()

    def set_status(self, status: int) -> "BaseStatusTracker":
        """
        Set the status of the task. Don't do this directly::

            self.value = self.make_value(self.job_id, ...)
        """
        _update_context[self.key]["value"] = {"old": self.value}
        self.value = self.make_value(status)
        _update_context[self.key]["value"]["new"] = self.value
        _update_context[self.key]["value"]["act"] = BaseStatusTracker.value.set(
            self.value
        )
        return self

    def set_update_time(
        self, update_time: T.Optional[datetime] = None
    ) -> "BaseStatusTracker":
        """
        Set the update time of the task. Don't do this directly::

            self.update_time = ...
        """
        _update_context[self.key]["update_time"] = {"old": self.update_time}
        if update_time is None:
            update_time = utc_now()
        self.update_time = update_time
        _update_context[self.key]["update_time"]["new"] = self.update_time
        _update_context[self.key]["update_time"][
            "act"
        ] = BaseStatusTracker.update_time.set(self.update_time)
        return self

    def set_retry_as_zero(self) -> "BaseStatusTracker":
        """
        Set the retry count to zero. Don't do this directly::

            self.retry = 0
        """
        _update_context[self.key]["retry"] = {"old": self.retry}
        self.retry = 0
        _update_context[self.key]["retry"]["new"] = self.retry
        _update_context[self.key]["retry"]["act"] = BaseStatusTracker.retry.set(
            self.retry
        )
        return self

    def set_retry_plus_one(self) -> "BaseStatusTracker":
        """
        Increase the retry count by one. Don't do this directly::

            self.retry += 1
        """
        _update_context[self.key]["retry"] = {"old": self.retry}
        self.retry += 1
        _update_context[self.key]["retry"]["new"] = self.retry
        _update_context[self.key]["retry"]["act"] = BaseStatusTracker.retry.set(
            BaseStatusTracker.retry + 1
        )
        return self

    def set_locked(self) -> "BaseStatusTracker":
        """
        Set the lock of the task. Don't do this directly::

            self.lock = ...
            self.lock_time = ...
        """
        _update_context[self.key]["lock"] = {"old": self.lock}
        _update_context[self.key]["lock_time"] = {"old": self.lock_time}
        self.lock = uuid.uuid4().hex
        self.lock_time = utc_now()
        _update_context[self.key]["lock"]["new"] = self.lock
        _update_context[self.key]["lock_time"]["new"] = self.lock_time
        _update_context[self.key]["lock"]["act"] = BaseStatusTracker.lock.set(self.lock)
        _update_context[self.key]["lock_time"]["act"] = BaseStatusTracker.lock_time.set(
            self.lock_time
        )
        return self

    def set_unlock(self) -> "BaseStatusTracker":
        """
        Set the lock of the task to None. Don't do this directly::

            self.lock = None
        """
        _update_context[self.key]["lock"] = {"old": self.lock}
        self.lock = None
        _update_context[self.key]["lock"]["new"] = self.lock
        _update_context[self.key]["lock"]["act"] = BaseStatusTracker.lock.set(self.lock)
        return self

    def set_data(self, data: T.Optional[dict]) -> "BaseStatusTracker":
        """
        Logically the data attribute should be mutable,
        make sure don't edit the old data directly
        for example, don't do this::

            self.data["foo"] = "bar"
            self.set_data(self.data)

        Please do this::

            new_data = self.data.copy()
            new_data["foo"] = "bar"
            self.set_data(new_data)
        """
        _update_context[self.key]["data"] = {"old": self.data}
        self.data = data
        _update_context[self.key]["data"]["new"] = self.data
        _update_context[self.key]["data"]["act"] = BaseStatusTracker.data.set(data)
        return self

    def set_errors(self, errors: T.Optional[dict]) -> "BaseStatusTracker":
        """
        Similar to :meth:`Tracker.set_data`. But it is for errors.
        """
        _update_context[self.key]["errors"] = {"old": self.errors}
        self.errors = errors
        _update_context[self.key]["errors"]["new"] = self.errors
        _update_context[self.key]["errors"]["act"] = BaseStatusTracker.errors.set(
            errors
        )
        return self

    def pre_start_hook(self):
        """
        A hook function that will be called before the task is started.
        """
        pass

    def post_start_hook(self):
        """
        A hook function that will be called after the task is finished.
        """
        pass

    @contextmanager
    def start(
        self,
        in_process_status: int,
        failed_status: int,
        success_status: int,
        ignore_status: int,
        debug: bool = False,
    ) -> "BaseStatusTracker":
        """
        A context manager to execute a task, and handle error automatically.

        1. It will set the status to the
        ``in_progress_status`` and set the lock. If the task is already locked,
        it will raise a :class:`TaskLockedError`.
        2. If the task succeeded, it will set the status to the ``success_status``.
        3. If the task fail, it will set the status to the ``failed_status`` and
            log the error to ``.errors`` attribute.
        4. If the task failed N times in a row, it will set the status to the
            ``ignore_status``.
        """
        self.pre_start_hook()

        if debug:
            print(
                "{msg:-^80}".format(
                    msg=(
                        f" ▶️ start task(job_id={self.job_id!r}, "
                        f"task_id={self.task_id!r}, "
                        f"status={self.status_name!r}) "
                    )
                )
            )

        # Handle concurrent lock
        if self.is_locked():
            raise TaskLockedError(f"Task {self.key} is locked.")

        # Handle ignore status
        if self.status == ignore_status:
            if debug:
                print(
                    f"↪️ the task is ignored, do nothing!"
                )
            raise TaskIgnoredError(
                f"Task {self.key} retry count already exceeded {self.MAX_RETRY}, "
                f"ignore it."
            )

        # mark as in progress
        with self.update_context():
            if debug:
                print(
                    f"🔓 set status {self.STATUS_ENUM.value_to_name(in_process_status)!r} "
                    f"and lock the task."
                )
            (self.set_status(in_process_status).set_update_time().set_locked())

        try:
            self._setup_update_context()
            # print("before yield")
            yield self
            # print("after yield")
            if debug:
                print(
                    f"✅ 🔐 task succeeded, "
                    f"set status {self.STATUS_ENUM.value_to_name(success_status)!r} and unlock the task."
                )
            (
                self.set_status(success_status)
                .set_update_time()
                .set_unlock()
                .set_retry_as_zero()
            )
            # print("end of success logic")
        except Exception as e:  # handling user code
            # print("before error handling")
            # reset the update context
            self._teardown_update_context()
            self._setup_update_context()
            if (self.retry + 1) >= self.MAX_RETRY:
                if debug:
                    print(
                        f"❌ 🔐 task failed {self.MAX_RETRY} times already, "
                        f"set status {self.STATUS_ENUM.value_to_name(ignore_status)!r} and unlock the task."
                    )
                self.set_status(ignore_status)
            else:
                if debug:
                    print(
                        f"❌ 🔐 task failed, "
                        f"set stats {self.STATUS_ENUM.value_to_name(failed_status)!r} and unlock the task."
                    )
                self.set_status(failed_status)
            (
                self.set_update_time()
                .set_unlock()
                .set_errors(
                    {
                        "error": repr(e),
                        "traceback": traceback.format_exc(limit=10),
                    }
                )
                .set_retry_plus_one()
            )
            # print("after error handling")
            raise e
        finally:
            # print("before finally")
            self._flush_update_context()
            self._teardown_update_context()

            if debug:
                print(
                    "{msg:-^80}".format(
                        msg=(
                            f" ⏹️ end task(job_id={self.job_id!r}, "
                            f"task_id={self.task_id!r}, "
                            f"status={self.status_name!r}) "
                        )
                    )
                )

            self.post_start_hook()
            # print("after finally")

    @classmethod
    def _get_status_index(cls) -> StatusAndCreateTimeIndex:
        """
        Detect the status index object.
        """
        if cls._status_and_create_time_index is None:
            for k, v in inspect.getmembers(cls):
                if isinstance(v, StatusAndCreateTimeIndex):
                    cls._status_and_create_time_index = v
                    return cls._status_and_create_time_index
            raise ValueError("you haven't defined a StatusAndTaskIdIndex")
        else:
            return cls._status_and_create_time_index

    @classmethod
    def _query_by_status(
        cls,
        status: T.Union[int, T.List[int]],
        limit: int = 10,
        older_task_first: bool = True,
        job_id: T.Optional[str] = None,
    ) -> IterProxy["BaseStatusTracker"]:
        """
        Get task items by status.
        """
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        if isinstance(status, list):
            status_list = status
        else:
            status_list = [status]
        for status in status_list:
            yield from cls._get_status_index().query(
                hash_key=cls.make_value(status, JOB_ID),
                scan_index_forward=older_task_first,
                limit=limit,
            )

    @classmethod
    def query_by_status(
        cls,
        status: T.Union[int, T.List[int]],
        limit: int = 10,
        older_task_first: bool = True,
        job_id: T.Optional[str] = None,
    ) -> IterProxy["BaseStatusTracker"]:
        """
        Query tasks by status code.

        :param status: single status code or list of status code
        :param limit: for each status code, how many items you want to return
        :param older_task_first: sort task by create_time in ascending or descending order
        :param job_id:

        .. versionchanged:: 5.3.4.7

            ``older_task_first`` parameter.
        """
        return IterProxy(
            cls._query_by_status(
                status=status,
                limit=limit,
                older_task_first=older_task_first,
                job_id=job_id,
            )
        )
