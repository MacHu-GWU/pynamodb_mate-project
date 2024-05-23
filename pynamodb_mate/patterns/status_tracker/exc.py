# -*- coding: utf-8 -*-


class TaskExecutionError(Exception):
    """
    The base class for errors raised during task execution.
    """

    @staticmethod
    def to_task(use_case_id: str, task_id: str) -> str:
        return f"Task(use_case_id={use_case_id!r}, task_id={task_id!r})"


class TaskIsNotInitializedError(TaskExecutionError):
    """
    Raised when a task is not initialized in DynamoDB table.
    """

    @classmethod
    def make(cls, use_case_id: str, task_id: str):
        return cls(
            f"{cls.to_task(use_case_id, task_id)} is not found in DynamoDB table, "
            "You have to run ``Task.make_and_save(task_id=...)`` to "
            "create an initial tracker item first."
        )


class TaskIsNotReadyToStartError(TaskExecutionError):
    """
    Raised when a task is not ready to start.

    There are two possible reasons:

    1. Task is locked.
    2. Task status is not pending or failed.
    """

    @classmethod
    def make(cls, use_case_id: str, task_id: str):
        return cls(
            f"{cls.to_task(use_case_id, task_id)} is not ready to start, "
            "either it is locked or status is not in 'pending' or 'failed'. "
            "You may use ``with Task.start(task_id=..., detailed_error=True) as execution_context:`` "
            "to get more details."
        )


class TaskLockedError(TaskExecutionError):
    """
    Raised when a task worker is trying to work on a locked task.
    """

    @classmethod
    def make(cls, use_case_id: str, task_id: str):
        return cls(f"{cls.to_task(use_case_id, task_id)} is locked")


class TaskAlreadySucceedError(TaskExecutionError):
    """
    Raised when a task is already in "succeeded" status.
    """

    @classmethod
    def make(cls, use_case_id: str, task_id: str):
        return cls(f"{cls.to_task(use_case_id, task_id)} is already succeeded.")


class TaskIgnoredError(TaskExecutionError):
    """
    Raised when a task is already in "ignored" status.
    """

    @classmethod
    def make(cls, use_case_id: str, task_id: str):
        return cls(f"{cls.to_task(use_case_id, task_id)} is ignored.")
