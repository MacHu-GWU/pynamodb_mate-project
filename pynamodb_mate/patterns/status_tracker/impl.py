# -*- coding: utf-8 -*-

"""
Implements the DynamoDB status tracking pattern.
"""

# standard lib
import typing as T
import enum
import uuid
import random
import inspect
import hashlib
import traceback
import dataclasses
from datetime import datetime, timezone, timedelta

# third party library
from iterproxy import IterProxy
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
    JSONAttribute,
)
from pynamodb.indexes import (
    GlobalSecondaryIndex,
    IncludeProjection,
)
from pynamodb.exceptions import UpdateError
from pynamodb.expressions.update import Action
from ...vendor.decorator import contextmanager

# pynamodb_mate stuff
from ...models import Model
from ...compat import cached_property
from ...type_hint import (
    REQUIRED_STR,
    REQUIRED_INT,
    REQUIRED_DATETIME,
)

# this module
from .exc import (
    TaskExecutionError,
    TaskIsNotInitializedError,
    TaskIsNotReadyToStartError,
    TaskLockedError,
    TaskAlreadySucceedError,
    TaskIgnoredError,
)


@dataclasses.dataclass
class ExecutionContext:
    """
    In our program design, we use Python's Context Manager to start a task's
    lifecycle and automatically update the status in the database based on
    the task's execution result (success or failure). This Execution Context
    is a container for all the contextual data in the lifecycle of
    executing a task, including any user data you need to save during
    the processing of this task.

    The :meth:`BaseTask.start` will return an instance of the
    :class:`ExecutionContext` object. You can use this object to set pending
    update actions.
    """

    task: "T_TASK" = dataclasses.field()
    _updates: T.Dict[str, Action] = dataclasses.field(default_factory=dict)

    def to_update_actions(self) -> T.List[Action]:
        return list(self._updates.values())

    def update(self):
        """
        Send in-memory to-update actions to DynamoDB, and set the task object
        as the updated task object.
        """
        # logically, this won't happen, but I add this check to make sure
        if self.task.lock is None:  # pragma: no cover
            raise ValueError
        res = self.task.update(
            actions=self.to_update_actions(),
            condition=_Task.lock == self.task.lock,
        )
        self.task = self.task.__class__.from_raw_data(res["Attributes"])

    def _set_status(self, status: int):
        """ """
        value = self.task.make_value(_task_id=self.task.task_id, status=status)
        self._updates[_Task.value.attr_name] = _Task.value.set(value)
        self._updates[_Task.status.attr_name] = _Task.status.set(status)
        return self

    def _set_update_time(self, update_time: T.Optional[datetime] = None):
        """
        Set the update time of the task. Don't do this directly::

            self.update_time = ...
        """
        if update_time is None:
            update_time = get_utc_now()
        self._updates[_Task.update_time.attr_name] = _Task.update_time.set(update_time)
        return self

    def _set_retry_as_zero(self):
        """
        Set the retry count to zero. Don't do this directly::

            self.retry = 0
        """
        self._updates[_Task.retry.attr_name] = _Task.retry.set(0)
        return self

    def _set_retry_plus_one(self):
        """
        Increase the retry count by one. Don't do this directly::

            self.retry += 1
        """
        self._updates[_Task.retry.attr_name] = _Task.retry.set(_Task.retry + 1)
        return self

    def _set_unlock(self):
        """
        Set the lock of the task to None. Don't do this directly::

            self.lock = None
        """
        self._updates[_Task.lock.attr_name] = _Task.lock.set(NOT_LOCKED)
        return self

    def set_data(self, data: T.Optional[dict]):
        """
        todo: update doc string
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
        self._updates[_Task.data.attr_name] = _Task.data.set(data)
        return self

    def _set_errors(self, errors: T.Optional[dict]):
        """
        Similar to :meth:`Tracker.set_data`. But it is for errors.
        """
        self._updates[_Task.errors.attr_name] = _Task.errors.set(errors)
        return self

    @contextmanager
    def begin_update(self):
        old_updates = self._updates.copy()
        try:
            yield self
        # revert the _updates to previous state if any exception raised
        except Exception as e:
            to_delete_keys = []
            for k in self._updates:
                if k in old_updates:
                    self._updates[k] = old_updates[k]
                else:
                    to_delete_keys.append(k)
            for k in to_delete_keys:
                del self._updates[k]
            raise e


class StatusNameEnum(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    failed = "failed"
    succeeded = "succeeded"
    ignored = "ignored"


class BaseStatusEnum(int, enum.Enum):
    """
    Base enum class to define the status code you want the tracker to track.

    The value of the status should be an integer. For example, you have a task
    that has the following status:

    .. code-block:: python

        class StatusEnum(BaseStatusEnum):
            pending = 0 # the task is defined but not started
            in_progress = 3 # the task is in progress
            failed = 6 # the task failed
            succeeded = 9 # the task succeeded
            ignored = 10 # the task already failed multiple times, it is ignored
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


def ensure_status_value(status: T.Union[int, BaseStatusEnum]) -> int:
    """
    Ensure it returns a integer value of a status.
    """
    if isinstance(status, BaseStatusEnum):
        return status.value
    else:
        return status


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def get_utc_now() -> datetime:
    """
    Get time aware utc now datetime object.
    """
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class StatusAndUpdateTimeIndex(GlobalSecondaryIndex):
    """
    GSI for query by job_id and status.

    .. versionchanged:: 5.3.4.7

        1. ``StatusAndTaskIdIndex`` is renamed to ``StatusAndCreateTimeIndex``
        2. it now uses ``create_time`` as the range key.
        3. it now uses AllProjection

    .. versionchanged:: 5.3.4.8

        1. ``StatusAndCreateTimeIndex`` is renamed to ``StatusAndUpdateTimeIndex``
        2. it now uses ``update_time`` as the range key.
        3. it now uses IncludeProjection
    """

    class Meta:
        index_name = "status_and_update_time-index"
        projection = IncludeProjection(["create_time"])

    # fmt: off
    value: T.Union[str, UnicodeAttribute] = UnicodeAttribute(hash_key=True)
    update_time: T.Union[datetime, UTCDateTimeAttribute] = UTCDateTimeAttribute(range_key=True)
    # fmt: on


@dataclasses.dataclass(frozen=True)
class TrackerConfig:
    """
    The per :class:`BaseTask` configuration object. Don't use the ``__init__``
    constructor directly. Use :meth:`TrackerConfig.make` instead.
    """

    use_case_id: str = dataclasses.field()
    sep: str = dataclasses.field()
    status_zero_pad: int = dataclasses.field()
    status_shard_zero_pad: int = dataclasses.field()
    max_retry: int = dataclasses.field()
    lock_expire_seconds: int = dataclasses.field()
    pending_status: int = dataclasses.field()
    in_progress_status: int = dataclasses.field()
    failed_status: int = dataclasses.field()
    succeeded_status: int = dataclasses.field()
    ignored_status: int = dataclasses.field()
    n_pending_shard: int = dataclasses.field()
    n_in_progress_shard: int = dataclasses.field()
    n_failed_shard: int = dataclasses.field()
    n_succeeded_shard: int = dataclasses.field()
    n_ignored_shard: int = dataclasses.field()
    more_pending_status: T.List[int] = dataclasses.field()
    traceback_stack_limit: int = dataclasses.field()
    status_enum: T.Type[BaseStatusEnum] = dataclasses.field()
    status_shards: T.Dict[int, int] = dataclasses.field()

    @classmethod
    def make(
        cls,
        use_case_id: str,
        pending_status: int,
        in_progress_status: int,
        failed_status: int,
        succeeded_status: int,
        ignored_status: int,
        n_pending_shard: int,
        n_in_progress_shard: int,
        n_failed_shard: int,
        n_succeeded_shard: int,
        n_ignored_shard: int,
        more_pending_status: T.Optional[T.Union[int, T.List[int]]] = None,
        sep: str = "____",
        status_zero_pad: int = 3,
        status_shard_zero_pad: int = 3,
        max_retry: int = 3,
        lock_expire_seconds: int = 300,
        traceback_stack_limit: int = 10,
    ):
        """
        Make a new status tracker configuration object. Don't use the ``__init__``
        directly.

        :param use_case_id: one DynamoDB table can serve multiple use cases.
            This is the common use_case_id for all tasks in this DynamoDB ORM model.
            you don't need to explicitly specify the job id in many API
        :param pending_status: pending status code in integer.
        :param in_progress_status: in_progress status code in integer.
        :param failed_status: failed status code in integer.
        :param succeeded_status: succeeded status code in integer.
        :param ignored_status: ignored status code in integer.
        :param n_pending_shard: number of GSI shard for this status, read
            https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
            for more information.
        :param n_in_progress_shard: number of GSI shard for this status.
        :param n_failed_shard: number of GSI shard for this status.
        :param n_succeeded_shard: number of GSI shard for this status,
            the succeeded status usually has the most shard, unless you will
            delete them from DynamoDB after succeeded.
        :param n_ignored_shard: number of GSI shard for this status.
        :param more_pending_status: additional pending status code that logically
            equal to "pending" status.
        :param sep: the separator string between job_id and task_id.
        :param status_zero_pad: how many digits the max status code have,
            it ensures that the encoded status can be used in comparison
        :param status_sharding_pad: how many digits the max shard number have,
            it ensures that the encoded status can be used in comparison
        :param max_retry: how many retry is allowed before we ignore it
        :param lock_expire_seconds: how long the lock will expire
        :param traceback_stack_limit: number of stack trace deep level to log
            when there's an error.
        """
        status_code_set = {
            pending_status,
            in_progress_status,
            failed_status,
            succeeded_status,
            ignored_status,
        }
        if len(status_code_set) != 5:
            raise ValueError("status code should be unique")

        class StatusEnum(BaseStatusEnum):
            pending = pending_status
            in_progress = in_progress_status
            failed = failed_status
            succeeded = succeeded_status
            ignored = ignored_status

        status_shards = {
            pending_status: n_pending_shard,
            in_progress_status: n_in_progress_shard,
            failed_status: n_failed_shard,
            succeeded_status: n_succeeded_shard,
            ignored_status: n_ignored_shard,
        }

        if more_pending_status is None:
            more_pending_status = []
        if isinstance(more_pending_status, int):
            more_pending_status = [more_pending_status]

        return cls(
            use_case_id=use_case_id,
            sep=sep,
            status_zero_pad=status_zero_pad,
            status_shard_zero_pad=status_shard_zero_pad,
            max_retry=max_retry,
            lock_expire_seconds=lock_expire_seconds,
            pending_status=pending_status,
            in_progress_status=in_progress_status,
            failed_status=failed_status,
            succeeded_status=succeeded_status,
            ignored_status=ignored_status,
            n_pending_shard=n_pending_shard,
            n_in_progress_shard=n_in_progress_shard,
            n_failed_shard=n_failed_shard,
            n_succeeded_shard=n_succeeded_shard,
            n_ignored_shard=n_ignored_shard,
            more_pending_status=more_pending_status,
            traceback_stack_limit=traceback_stack_limit,
            status_enum=StatusEnum,
            status_shards=status_shards,
        )


NOT_LOCKED = "__not_locked__"


class BaseTask(Model):
    """
    The DynamoDB ORM model for the status tracking of a task. You can use one
    DynamoDB table for multiple status tracking use cases.

    Concepts:

    - use case: a high-level description of a job, the similar task on different
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
    :param update_time: when the task item is created
    :param update_time: when the task status is updated
    :param retry: how many times the task has been retried
    :param lock: a concurrency control mechanism. It is an uuid string.
    :param lock_time: when this task is locked.
    :param data: arbitrary data in python dictionary.
    :param errors: arbitrary error data in python dictionary.
    """

    # fmt: off
    key: REQUIRED_STR = UnicodeAttribute(hash_key=True)
    value: REQUIRED_STR = UnicodeAttribute()
    status: REQUIRED_INT = NumberAttribute()
    create_time: REQUIRED_DATETIME = UTCDateTimeAttribute(default=get_utc_now)
    update_time: REQUIRED_DATETIME = UTCDateTimeAttribute(default=get_utc_now)
    retry: REQUIRED_INT = NumberAttribute(default=0)
    lock: REQUIRED_STR = UnicodeAttribute(default=NOT_LOCKED)
    lock_time: REQUIRED_DATETIME = UTCDateTimeAttribute(default=EPOCH)
    data: T.Optional[T.Union[dict, JSONAttribute]] = JSONAttribute(default=lambda: dict(), null=True)
    errors: T.Optional[T.Union[dict, JSONAttribute]] = JSONAttribute(default=lambda: {"history": []}, null=True)
    # fmt: on

    _status_and_update_time_index: T.Optional[StatusAndUpdateTimeIndex] = None

    config: TrackerConfig

    @classmethod
    def make_key(
        cls,
        task_id: str,
        _use_case_id: T.Optional[str] = None,
    ) -> str:
        """
        Join the job_id and task_id to create the DynamoDB hash key.

        :param task_id: the task id.
        :param _use_case_id: in most of the case, you should not set this parameter manually,
            because it is already defined in :attr:`TrackerConfig.job_id`.
            But if you want to manually set the job_id, you can use this parameter.
        """
        if _use_case_id is None:
            _use_case_id = cls.config.use_case_id
        return f"{_use_case_id}{cls.config.sep}{task_id}"

    @classmethod
    def make_value(
        cls,
        status: int,
        _use_case_id: T.Optional[str] = None,
        _task_id: T.Optional[str] = None,
        _shard_id: T.Optional[int] = None,
    ) -> str:
        """
        Join the job_id and status to create the ``value`` attribute.

        :param status: the status code.
        :param _use_case_id: in most of the case, you should not set this parameter manually,
            because it is already defined in :attr:`TrackerConfig.job_id`.
            But if you want to manually set the job_id, you can use this parameter.
        :param _task_id: the task id.
        :param _shard_id: the shard id.
        """
        if _use_case_id is None:
            _use_case_id = cls.config.use_case_id
        if _shard_id is None:
            if _task_id is None:
                raise ValueError
            key = cls.make_key(task_id=_task_id, _use_case_id=_use_case_id)
            _shard_id = (hash(key) % cls.config.status_shards[status]) + 1
        return (
            f"{_use_case_id}"
            f"{cls.config.sep}"
            f"{str(status).zfill(cls.config.status_zero_pad)}"
            f"{cls.config.sep}"
            f"{str(_shard_id).zfill(cls.config.status_shard_zero_pad)}"
        )

    @cached_property
    def use_case_id(self) -> str:
        return self.key.split(self.config.sep, 1)[0]

    @cached_property
    def task_id(self) -> str:
        """
        Return the task_id part of the key. It should be unique with in a job.
        """
        return self.key.split(self.config.sep, 1)[1]

    @property
    def shard_id(self) -> int:
        """
        Return the status value of the task.
        """
        return int(self.value.split(self.config.sep, 1)[1].split(self.config.sep, 1)[1])

    @property
    def status_name(self) -> str:
        """
        Return the status name of the task. If you don't set the Status enum
        class to the ``STATUS_ENUM`` class attribute, it returns the integer
        value of the status. If you did so, it returns the human-friendly
        status name.
        """
        return self.__class__.config.status_enum.value_to_name(self.status)

    def is_pending(self) -> bool:
        return self.status == self.config.pending_status

    def is_in_progress(self) -> bool:
        return self.status == self.config.in_progress_status

    def is_failed(self) -> bool:
        return self.status == self.config.failed_status

    def is_succeeded(self) -> bool:
        return self.status == self.config.succeeded_status

    def is_ignored(self) -> bool:
        return self.status == self.config.ignored_status

    @classmethod
    def get_one_or_none(
        cls,
        task_id: str,
        consistent_read: bool = False,
        attributes_to_get: T.Optional[T.Sequence[str]] = None,
        _use_case_id: T.Optional[str] = None,
    ) -> T.Optional["BaseTask"]:
        """
        Get one item by task_id. If the item does not exist, return None.
        """
        return super().get_one_or_none(
            hash_key=cls.make_key(task_id, _use_case_id),
            consistent_read=consistent_read,
            attributes_to_get=attributes_to_get,
        )

    # def is_item_exists(self) -> bool:
    #     """
    #     Check if this Dynamodb item exists.
    #     """
    #     return (
    #         self.get_one_or_none(
    #             task_id=self.task_id,
    #             attributes_to_get=[
    #                 "key",
    #             ],
    #         )
    #         is not None
    #     )

    @classmethod
    def make(
        cls,
        task_id: str,
        data: T.Optional[dict] = None,
        _use_case_id: T.Optional[str] = None,
        _status: T.Optional[int] = None,
        _shard_id: T.Optional[int] = None,
        **kwargs,
    ):
        """
        A factory method to create new instance of a tracker.

        :param task_id: the task id.
        :param data: the data attribute.
        :param _use_case_id: in most of the case, you should not set this parameter manually,
            because it is already defined in :attr:`TrackerConfig.job_id`.
            But if you want to manually set the job_id, you can use this parameter.
        :param _status: the status code, if not provided, it will use the pending status.
        :param _shard_id: the shard id, if not provided, it will be calculated.
        :param kwargs: additional attributes.
        """
        if _status is None:
            _status = cls.config.pending_status
        attributes = dict(
            key=cls.make_key(task_id=task_id, _use_case_id=_use_case_id),
            value=cls.make_value(
                status=_status,
                _use_case_id=_use_case_id,
                _task_id=task_id,
                _shard_id=_shard_id,
            ),
            status=_status,
        )
        if data is not None:
            attributes["data"] = data
        return cls(**attributes, **kwargs)

    @classmethod
    def make_and_save(
        cls,
        task_id: str,
        data: T.Optional[dict] = None,
        _use_case_id: T.Optional[str] = None,
        _status: T.Optional[int] = None,
        _shard_id: T.Optional[int] = None,
        **kwargs,
    ):
        """
        Similar to :meth:`Tracker.make`, but it will save the item to the DynamoDB.

        :param task_id: the task id.
        :param data: the data attribute.
        :param _use_case_id: in most of the case, you should not set this parameter manually,
            because it is already defined in :attr:`TrackerConfig.job_id`.
            But if you want to manually set the job_id, you can use this parameter.
        :param _status: the status code, if not provided, it will use the todo_status.
        :param _shard_id: the shard id, if not provided, it will be calculated.
        :param kwargs: additional attributes.
        """
        task = cls.make(
            task_id=task_id,
            data=data,
            _use_case_id=_use_case_id,
            _status=_status,
            _shard_id=_shard_id,
            **kwargs,
        )
        task.save()
        return task

    @classmethod
    def delete_tasks_by_use_case_id(
        cls,
        use_case_id: T.Optional[str] = None,
    ) -> int:
        """
        Delete all item belongs to specific job.

        Note: this method is expensive, it will scan a lot of items.
        """
        if use_case_id is None:
            use_case_id = cls.config.use_case_id
        ith = 0
        with cls.batch_write() as batch:
            for ith, item in enumerate(
                cls.scan(
                    filter_condition=cls.key.startswith(use_case_id),
                    attributes_to_get=[
                        "key",
                    ],
                ),
                start=1,
            ):
                batch.delete(item)
        return ith

    @classmethod
    def count_tasks_by_use_case_id(
        cls,
        use_case_id: T.Optional[str] = None,
    ):
        """
        Count number of items belong to specific job.

        Note:

        This method is expensive, it will scan the entire table, and consume
        the read capacity unit that equals to the total amount of data
        (DynamoDB considers the size of the items that are evaluated,
        not the size of the items returned by the scan.).

        If you really need to query by job_id efficiently, consider these two options:

        1. use :meth:`BaseTask.query_by_status(status=[status1, status2, ...], use_case_id=your_use_case_id) <BaseTask.query_by_status>`.
        2. add an attribute called ``use_case_id``, and create a GSI using the
            `Using Global Secondary Index write sharding for selective table queries <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes-gsi-sharding.html>`_
            strategy.
        """
        if use_case_id is None:
            use_case_id = cls.config.use_case_id
        ith = 0
        for ith, item in enumerate(
            cls.scan(
                filter_condition=cls.key.startswith(use_case_id),
                attributes_to_get=[
                    "key",
                ],
            ),
            start=1,
        ):
            pass
        return ith

    def is_locked(
        self,
        expected_lock: T.Optional[str] = None,
        utc_now: T.Optional[datetime] = None,
    ) -> bool:
        """
        Check if the task is locked.

        :param expected_lock: if provided, we consider it is not locked if the
            server side lock is the same as the expected lock.
        :param utc_now: if provided, use this value as the "now" time.
        """
        # if server side lock is None, it is not locked
        if self.lock == NOT_LOCKED:
            return False
        else:
            # if expected_lock is provided and match the server side lock,
            # it is not locked
            if expected_lock is not None:
                return not (self.lock == expected_lock)
            # check if the lock is expired
            if utc_now is None:
                utc_now = get_utc_now()
            lock_elapsed = (utc_now - self.lock_time).total_seconds()
            return lock_elapsed < self.__class__.config.lock_expire_seconds

    @classmethod
    @contextmanager
    def start(
        cls,
        task_id: str,
        more_pending_status: T.Optional[T.Union[int, T.List[int]]] = None,
        detailed_error: bool = False,
        debug: bool = False,
    ):
        """
        This is the **CORE API** for status tracker. It is a context manager that
        where you can put your task execution logic under it. It does the following:

        1. It will set the status to the
            ``in_progress_status`` and set the lock. If the task is already locked,
            it will raise a :class:`TaskLockedError`.
        2. If the task succeeded, it will set the status to the ``succeeded_status``.
        3. If the task fail, it will set the status to the ``failed_status`` and
            log the error to ``.errors`` attribute.
        4. If the task failed N times in a row, it will set the status to the
            ``ignored_status``.
        """
        if debug:  # pragma: no cover
            print(
                "{msg:-^120}".format(
                    msg=" ▶️ start Task({}, {})".format(
                        f"use_case_id={cls.config.use_case_id!r}",
                        f"task_id={task_id!r})",
                    ),
                )
            )

        # Handle concurrent lock
        task = cls.make(task_id=task_id)
        lock = uuid.uuid4().hex
        lock_time = get_utc_now()

        if debug:  # pragma: no cover
            print(
                f"🔓 set status {StatusNameEnum.in_progress.value!r} and lock the task."
            )

        try:
            # create the condition that the current task status is "ready to start",
            # in other words, if the status is any of "pending", "failed" or "more_pending_status".
            is_ready_to_start = (cls.status == cls.config.pending_status) | (
                cls.status == cls.config.failed_status
            )
            if more_pending_status is None:
                more_pending_status = cls.config.more_pending_status
            elif isinstance(more_pending_status, int):
                more_pending_status = [more_pending_status]
            else:  # pragma: no cover
                pass
            if more_pending_status:
                for status in more_pending_status:
                    is_ready_to_start |= cls.status == status
            res = task.update(
                actions=[
                    cls.value.set(
                        cls.make_value(
                            status=cls.config.in_progress_status,
                            _task_id=task_id,
                        )
                    ),
                    cls.status.set(cls.config.in_progress_status),
                    cls.lock.set(lock),
                    cls.lock_time.set(lock_time),
                ],
                # we get the lock only if the task is not locked and
                # task is in todo_status or failed_status
                # See: https://pynamodb.readthedocs.io/en/latest/conditional.html
                # to know about the condition expression
                condition=(
                    (
                        (cls.lock == NOT_LOCKED)
                        | (cls.lock == lock)
                        | (
                            cls.lock_time
                            < (
                                lock_time
                                - timedelta(seconds=cls.config.lock_expire_seconds)
                            )
                        )
                    )
                    & is_ready_to_start
                ),
            )
        except UpdateError as e:
            # print(f"--- enter failed to get lock error handling logic ---") # for debug only
            # print(f"{e.cause_response_code = }") # for debug only
            if e.cause_response_code == "ConditionalCheckFailedException":
                if detailed_error:
                    task_ = cls.get_one_or_none(task_id=task_id)
                    if task_ is None:
                        error = TaskIsNotInitializedError.make(
                            use_case_id=cls.config.use_case_id,
                            task_id=task_id,
                        )
                        if debug:  # pragma: no cover
                            print(
                                "❌ task failed to get lock, because it is not initialized yet."
                            )
                    elif task_.is_locked(expected_lock=lock, utc_now=lock_time):
                        error = TaskLockedError.make(
                            use_case_id=cls.config.use_case_id,
                            task_id=task_id,
                        )
                        if debug:  # pragma: no cover
                            print(
                                "❌ task failed to get lock, because it is already locked by another worker."
                            )
                    elif task_.is_succeeded():
                        error = TaskAlreadySucceedError.make(
                            use_case_id=cls.config.use_case_id,
                            task_id=task_id,
                        )
                        if debug:  # pragma: no cover
                            print(
                                "❌ task failed to get lock, because it is already succeeded."
                            )
                    elif task_.is_ignored():
                        error = TaskIgnoredError.make(
                            use_case_id=cls.config.use_case_id,
                            task_id=task_id,
                        )
                        if debug:  # pragma: no cover # pragma: no cover
                            print("❌ task failed to get lock, because it is ignored.")
                    elif task_.status not in more_pending_status:
                        if more_pending_status:
                            error = TaskIsNotReadyToStartError(
                                f"{TaskIsNotReadyToStartError.to_task(cls.config.use_case_id, task_id)} is not ready to start, "
                                f"the status {task_.status} is not in the ready-to-start status {more_pending_status}."
                            )
                            if debug:  # pragma: no cover
                                print(
                                    f"❌ task is not ready to start, "
                                    f"the status {task_.status} is not in the ready-to-start status: {more_pending_status}."
                                )
                        else:
                            error = TaskIsNotReadyToStartError.make(
                                use_case_id=cls.config.use_case_id,
                                task_id=task_id,
                            )
                            if debug:  # pragma: no cover
                                print(
                                    "❌ task is not ready to start yet, "
                                    "either it is locked or status is not in 'pending' or 'failed'."
                                )
                    else:  # pragma: no cover
                        error = NotImplementedError(
                            f"You found a bug! This error should be handled but not implemented yet, "
                            f"please report to ...; error {e!r}"
                        )
                else:
                    error = TaskIsNotReadyToStartError.make(
                        use_case_id=cls.config.use_case_id,
                        task_id=task_id,
                    )
                    if debug:  # pragma: no cover
                        print(
                            "❌ task is not ready to start yet, "
                            "either it is locked or status is not in 'pending' or 'failed' or allowed status."
                        )
            else:  # pragma: no cover
                error = e
            if debug:  # pragma: no cover
                print(
                    "{msg:-^120}".format(
                        msg=" ⏹️ end Task({}, {})".format(
                            f"use_case_id={cls.config.use_case_id!r}",
                            f"task_id={task_id!r})",
                        ),
                    )
                )
            raise error

        # See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/update_item.html
        # to know about response of the update_item API
        task_updated = cls.from_raw_data(res["Attributes"])
        execution_context = ExecutionContext(task=task_updated)

        try:
            # print("before yield")
            with execution_context.begin_update():
                yield execution_context
            # print("after yield")
            if debug:  # pragma: no cover
                print(
                    f"✅ 🔐 task succeeded, set status {StatusNameEnum.succeeded.value!r} and unlock the task."
                )
            with execution_context.begin_update():
                execution_context._set_status(cls.config.succeeded_status)
                execution_context._set_update_time()
                execution_context._set_unlock()
                execution_context._set_retry_as_zero()
            execution_context.update()
            # print("end of success logic") # for debug only
        except Exception as e:  # handling user code
            # print("before error handling")
            # execution_context._set_status(cls.config.failed_status)
            update_time = get_utc_now()
            with execution_context.begin_update():
                execution_context._set_update_time(update_time)
                execution_context._set_unlock()
                execution_context._set_retry_plus_one()
                task_updated.errors["history"].append(
                    {
                        "nth_retry": task_updated.retry + 1,
                        "update_time": update_time.isoformat(),
                        "error": repr(e),
                        "traceback": traceback.format_exc(
                            limit=cls.config.traceback_stack_limit
                        ),
                    }
                )
                execution_context._set_errors(task_updated.errors)
            if (task_updated.retry + 1) >= cls.config.max_retry:
                if debug:  # pragma: no cover
                    print(
                        f"❌ 🔐 task failed {cls.config.max_retry} times already, "
                        f"set status {StatusNameEnum.ignored.value!r} and unlock the task."
                    )
                with execution_context.begin_update():
                    execution_context._set_status(cls.config.ignored_status)
            else:
                if debug:  # pragma: no cover
                    print(
                        f"❌ 🔐 task failed, "
                        f"set stats {StatusNameEnum.failed.value!r} and unlock the task."
                    )
                with execution_context.begin_update():
                    execution_context._set_status(cls.config.failed_status)
            execution_context.update()
            # print("after error handling")
            raise e
        finally:
            # print("before finally")
            if debug:  # pragma: no cover
                print(
                    "{msg:-^120}".format(
                        msg=" ⏹️ end Task({}, {}, {}) (aka {})".format(
                            f"use_case_id={cls.config.use_case_id!r}",
                            f"task_id={task_id!r})",
                            f"status={task_updated.status})",
                            repr(task_updated.status_name),
                        ),
                    )
                )
        # print("after finally")

    @classmethod
    def _get_status_index(cls, _is_test: bool = False) -> StatusAndUpdateTimeIndex:
        """
        Detect the status index object.
        """
        if cls._status_and_update_time_index is None:  # pragma: no cover
            # just for local unit test, keep it in the source code intentionally
            if _is_test:  # pragma: no cover
                print("call _get_status_index() ...")
            for k, v in inspect.getmembers(cls):
                if isinstance(v, StatusAndUpdateTimeIndex):
                    cls._status_and_update_time_index = v
                    return cls._status_and_update_time_index
            raise ValueError("you haven't defined a 'StatusAndCreateTimeIndex'")
        else:
            return cls._status_and_update_time_index

    @classmethod
    def _query_by_status(
        cls,
        status: T.Union[
            T.Union[int, BaseStatusEnum],
            T.List[T.Union[int, BaseStatusEnum]],
        ],
        limit: int = 10,
        older_task_first: bool = True,
        use_case_id: T.Optional[str] = None,
    ) -> IterProxy["BaseTask"]:
        """
        Get task items by status.
        """
        if use_case_id is None:
            use_case_id = cls.config.use_case_id

        if isinstance(status, list):
            status_list = status
        else:
            status_list = [status]
        processed_status_list: T.List[int] = [
            ensure_status_value(status) for status in status_list
        ]

        # use index to query by status and aggregate the results
        index = cls._get_status_index()
        for status in processed_status_list:
            n_shard = cls.config.status_shards[status]
            for shard_id in range(1, 1 + n_shard):
                yield from index.query(
                    hash_key=cls.make_value(
                        status=status,
                        _use_case_id=use_case_id,
                        _shard_id=shard_id,
                    ),
                    scan_index_forward=older_task_first,
                    limit=limit,
                )

    @classmethod
    def query_by_status(
        cls,
        status: T.Union[
            T.Union[int, BaseStatusEnum],
            T.List[T.Union[int, BaseStatusEnum]],
        ],
        limit: int = 10,
        older_task_first: bool = True,
        auto_refresh: bool = False,
        use_case_id: T.Optional[str] = None,
    ) -> IterProxy["BaseTask"]:
        """
        Query tasks by status code.

        :param status: single status code or list of status code
        :param limit: for each status code, how many items you want to return
        :param older_task_first: sort task by update_time in ascending or descending order
        :param auto_refresh: by default, the returned task object only include
            DynamoDB key attributes. If you set auto_refresh = True,
            this method automatically refresh to  get the full task object for you.

        :param _use_case_id:
        """
        result_iterator = cls._query_by_status(
            status=status,
            limit=limit,
            older_task_first=older_task_first,
            use_case_id=use_case_id,
        )

        def new_iterator():
            for item in result_iterator:
                item.refresh()
                yield item

        if auto_refresh:
            return IterProxy(new_iterator())
        else:
            return IterProxy(result_iterator)

    @classmethod
    def query_for_unfinished(
        cls,
        limit: int = 10,
        older_task_first: bool = True,
        auto_refresh: bool = False,
        use_case_id: T.Optional[str] = None,
    ) -> IterProxy["BaseTask"]:
        """
        Query tasks that are not finished yet, in other words, the status is
        either pending or failed.

        :param limit: for each status code, how many items you want to return
        :param older_task_first: sort task by update_time in ascending or descending order
        :param auto_refresh: by default, the returned task object only include
            DynamoDB key attributes. If you set auto_refresh = True,
            this method automatically refresh to  get the full task object for you.
        """
        return cls.query_by_status(
            status=[
                cls.config.pending_status,
                cls.config.failed_status,
            ],
            limit=limit,
            older_task_first=older_task_first,
            auto_refresh=auto_refresh,
            use_case_id=use_case_id,
        )


T_TASK = T.TypeVar("T_TASK", bound=BaseTask)

_Task = BaseTask
