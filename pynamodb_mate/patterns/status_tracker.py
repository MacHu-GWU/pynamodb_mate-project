# -*- coding: utf-8 -*-

import typing as T
import enum
import uuid
import traceback
import dataclasses
from contextlib import contextmanager

from datetime import datetime, timezone

from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
    JSONAttribute,
)
from pynamodb.indexes import (
    GlobalSecondaryIndex,
    KeysOnlyProjection,
)
from pynamodb.settings import OperationSettings

from ..models import Model
from ..compat import cached_property


class BaseStatusEnum(int, enum.Enum):
    @property
    def status_name(self) -> str:
        return self.name

    @classmethod
    def from_value(cls, value: int) -> "BaseStatusEnum":
        return cls(value)

    @classmethod
    def value_to_name(cls, value: int) -> str:
        return cls.from_value(value).name

    @classmethod
    def values(cls) -> T.List[int]:
        return [status.value for status in cls]


ZERO_PADDING = 4


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class StatusAndTaskIdIndex(GlobalSecondaryIndex):
    """
    GSI for query by job_id and status
    """

    class Meta:
        index_name = "status_and_task_id-index"
        projection = KeysOnlyProjection()

    value: T.Union[str, UnicodeAttribute] = UnicodeAttribute(hash_key=True)
    key: T.Union[str, UnicodeAttribute] = UnicodeAttribute(range_key=True)


class LockError(Exception):
    """
    Raised when a task worker is trying to work on a locked task.
    """

    pass


class IgnoreError(Exception):
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
    @classmethod
    def from_dict(cls, dct: dict):
        return cls(**dct)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class BaseData(BaseDataClass):
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
        for a task.
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
    """

    key: T.Union[str, UnicodeAttribute] = UnicodeAttribute(hash_key=True)
    value: T.Union[str, UnicodeAttribute] = UnicodeAttribute()
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

    status_and_task_id_index: StatusAndTaskIdIndex

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

    @classmethod
    def make_key(
        cls,
        task_id: str,
        job_id: T.Optional[str] = None,
    ) -> str:
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        return f"{JOB_ID}{cls.SEP}{task_id}"

    @classmethod
    def make_value(
        cls,
        status: int,
        job_id: T.Optional[str] = None,
    ) -> str:
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        return f"{JOB_ID}{cls.SEP}{str(status).zfill(cls.STATUS_ZERO_PAD)}"

    @cached_property
    def job_id(self) -> str:
        return self.key.split(self.SEP)[0]

    @cached_property
    def task_id(self) -> str:
        return self.key.split(self.SEP)[1]

    @property
    def status(self) -> int:
        return int(self.value.split(self.SEP)[1])

    @classmethod
    def get_one_or_none(
        cls,
        task_id: str,
        consistent_read: bool = False,
        attributes_to_get: T.Optional[T.Sequence[str]] = None,
        settings: OperationSettings = OperationSettings.default,
        job_id: T.Optional[str] = None,
    ) -> T.Optional["BaseStatusTracker"]:
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
        A factory method to create new instance of a tracker. It won't save
        to DynamoDB.
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
        A factory method to create new instance of a tracker and save it to
        DynamoDB.
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

    @contextmanager
    def start(
        self,
        in_process_status: int,
        failed_status: int,
        success_status: int,
        ignore_status: int,
    ) -> "BaseStatusTracker":
        # Handle concurrent lock
        if self.is_locked():
            raise LockError(f"Task {self.key} is locked.")

        # Handle ignore status
        if self.status == ignore_status:
            raise IgnoreError(
                f"Task {self.key} retry count already exceeded {self.MAX_RETRY}, "
                f"ignore it."
            )

        # mark as in progress
        with self.update_context():
            (self.set_status(in_process_status).set_update_time().set_locked())

        try:
            self._setup_update_context()
            # print("before yield")
            yield self
            # print("after yield")
            (
                self.set_status(success_status)
                .set_update_time()
                .set_unlock()
                .set_retry_as_zero()
            )
            # print("end of success logic")
        except Exception as e:  # handling user code
            # print("begin of error handling logic")
            # reset the update context
            self._teardown_update_context()
            self._setup_update_context()
            (
                self.set_status(failed_status)
                .set_update_time()
                .set_unlock()
                .set_errors(
                    {
                        "error": repr(e),
                        "traceback": traceback.format_exc(limit=10),
                    }
                )
                .set_retry_plus_one()
            )
            if self.retry >= self.MAX_RETRY:
                self.set_status(ignore_status)
            # print("end of error handling logic")
            raise e
        finally:
            # print("begin of finally")
            self._flush_update_context()
            self._teardown_update_context()
            # print("end of finally")

    @classmethod
    def query_by_status(
        cls,
        status: T.Union[int, T.List[int]],
        limit: int = 10,
        job_id: T.Optional[str] = None,
    ) -> T.Iterable["BaseStatusTracker"]:
        JOB_ID = cls.JOB_ID if job_id is None else job_id
        if isinstance(status, list):
            status_list = status
        else:
            status_list = [status]
        for status in status_list:
            yield from cls.status_and_task_id_index.query(
                hash_key=cls.make_value(status, JOB_ID),
                limit=limit,
            )
