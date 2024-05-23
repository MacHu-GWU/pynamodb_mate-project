# -*- coding: utf-8 -*-

import pytest
import time

import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import IS_CI, PY_VER, PYNAMODB_VER
from pynamodb_mate.tests.base_test import BaseTest
from pynamodb_mate.patterns.status_tracker.impl import (
    ExecutionContext,
    get_utc_now,
    StatusNameEnum,
    BaseStatusEnum,
    TrackerConfig,
    StatusAndUpdateTimeIndex,
    BaseTask,
    TaskExecutionError,
    TaskIsNotInitializedError,
    TaskIsNotReadyToStartError,
    TaskLockedError,
    TaskAlreadySucceedError,
    TaskIgnoredError,
)
from rich import print as rprint


# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------


class UserError(Exception):
    pass


class Task(BaseTask):
    class Meta:
        table_name = f"pynamodb-mate-test-status-tracker-v2-{PY_VER}-{PYNAMODB_VER}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    status_and_update_time_index = StatusAndUpdateTimeIndex()


class Step1StatusEnum(BaseStatusEnum):
    pending = 10
    in_progress = 20
    failed = 30
    succeeded = 40
    ignored = 50


class Step2StatusEnum(BaseStatusEnum):
    pending = 40
    in_progress = 70
    failed = 80
    succeeded = 90
    ignored = 100


class Step1(Task):
    status_and_update_time_index = StatusAndUpdateTimeIndex()

    config = TrackerConfig.make(
        use_case_id="test",
        pending_status=Step1StatusEnum.pending.value,
        in_progress_status=Step1StatusEnum.in_progress.value,
        failed_status=Step1StatusEnum.failed.value,
        succeeded_status=Step1StatusEnum.succeeded.value,
        ignored_status=Step1StatusEnum.ignored.value,
        n_pending_shard=5,
        n_in_progress_shard=5,
        n_failed_shard=5,
        n_succeeded_shard=10,
        n_ignored_shard=5,
    )


class Step2(Task):
    status_and_update_time_index = StatusAndUpdateTimeIndex()

    config = TrackerConfig.make(
        use_case_id="test",
        pending_status=Step2StatusEnum.pending.value,
        in_progress_status=Step2StatusEnum.in_progress.value,
        failed_status=Step2StatusEnum.failed.value,
        succeeded_status=Step2StatusEnum.succeeded.value,
        ignored_status=Step2StatusEnum.ignored.value,
        n_pending_shard=5,
        n_in_progress_shard=5,
        n_failed_shard=5,
        n_succeeded_shard=10,
        n_ignored_shard=5,
    )


class TestStatusEnum:
    def test(self):
        assert Step1StatusEnum.pending.status_name == StatusNameEnum.pending.value
        assert Step1StatusEnum.from_value(10) == Step1StatusEnum.pending
        assert Step1StatusEnum.value_to_name(10) == StatusNameEnum.pending.value
        assert Step1StatusEnum.values() == [
            Step1StatusEnum.pending,
            Step1StatusEnum.in_progress,
            Step1StatusEnum.failed,
            Step1StatusEnum.succeeded,
            Step1StatusEnum.ignored,
        ]


class TestExecutionContext:
    def test_context_manager(self):
        ctx = ExecutionContext(task=Step1(key="test"))
        assert ctx._updates == {}

        ctx.set_data(data={"version": 1})
        assert '{"version": 1}' in str(ctx._updates["data"])

        with pytest.raises(Exception):
            with ctx.begin_update():
                ctx.set_data(data={"version": 2})
                raise Exception
        assert '{"version": 1}' in str(ctx._updates["data"])
        assert '{"version": 2}' not in str(ctx._updates["data"])


class TestTrackerConfig:
    def test(self):
        with pytest.raises(ValueError):
            TrackerConfig.make(
                use_case_id="test",
                pending_status=10,
                in_progress_status=10,
                failed_status=10,
                succeeded_status=10,
                ignored_status=10,
                n_pending_shard=1,
                n_in_progress_shard=1,
                n_failed_shard=1,
                n_succeeded_shard=1,
                n_ignored_shard=1,
            )


class Base(BaseTest):

    model_list = [
        Task,
        Step1,
        Step2,
    ]

    def test(self):
        self._test_constructor()
        self._test_1_happy_path()
        self._test_2_lock_mechanism()
        self._test_3_retry_and_ignore()
        self._test_4()

        # self._test_11_query_by_status()

    def _test_constructor(self):
        step1 = Step1.make(task_id="t-0")
        assert step1.use_case_id == "test"
        assert step1.task_id == "t-0"
        assert step1.status == Step1StatusEnum.pending.value
        assert step1.status_name == StatusNameEnum.pending.value
        assert step1.shard_id in list(range(1, 1 + Step1.config.n_pending_shard))

        step1 = Step1.make(
            task_id="t-0",
            _use_case_id="test1",
            _status=Step1StatusEnum.failed.value,
            _shard_id=1,
        )
        assert step1.use_case_id == "test1"
        assert step1.task_id == "t-0"
        assert step1.status == Step1StatusEnum.failed.value
        assert step1.status_name == StatusNameEnum.failed.value
        assert step1.shard_id == 1

    def _test_1_happy_path(self):
        """
        This test is to simulate
        """
        task_id = "t-1"

        # ----------------------------------------------------------------------
        # run Step 1, it will succeed
        # ----------------------------------------------------------------------
        utc_now = get_utc_now()

        # create a new task
        step1 = Step1.make_and_save(task_id=task_id, data={"version": 0})
        assert step1.status == Step1StatusEnum.pending.value
        assert step1.is_locked() is False

        step1 = Step1.get_one_or_none(task_id=task_id)
        assert step1.status == Step1StatusEnum.pending.value
        assert step1.is_locked() is False

        # start the job, this time it will succeed
        exec_ctx: ExecutionContext
        with Step1.start(task_id, debug=False) as exec_ctx:
            # check if the task status became "in progress"
            assert exec_ctx.task.is_in_progress()
            # check if the task update time got updated
            assert exec_ctx.task.update_time > utc_now
            # check if the task is locked
            assert exec_ctx.task.is_locked() is True
            # do some work
            exec_ctx.set_data({"version": 1})

        # check the in-memory updated task
        # check if the task status became "succeeded"
        assert exec_ctx.task.is_succeeded()
        # check if the task update time got updated
        assert exec_ctx.task.update_time > utc_now
        # check if the task is locked
        assert exec_ctx.task.is_locked() is False
        # check if the task data got updated
        assert exec_ctx.task.data == {"version": 1}
        # check if the task retry count is 0
        assert exec_ctx.task.retry == 0
        # check if the task errors is empty
        assert len(exec_ctx.task.errors["history"]) == 0

        # check the database side updated task
        step1 = Step1.get_one_or_none(task_id=task_id)
        # check if the task status became "succeeded"
        assert step1.is_succeeded()
        # check if the task update time got updated
        assert step1.update_time > utc_now
        # check if the task is locked
        assert step1.is_locked() is False
        # check if the task data got updated
        assert step1.data == {"version": 1}
        # check if the task retry count is 0
        assert step1.retry == 0
        # check if the task errors is empty
        assert len(step1.errors["history"]) == 0

        # ----------------------------------------------------------------------
        # run Step 1, it will fail
        # ----------------------------------------------------------------------
        with pytest.raises(TaskIsNotReadyToStartError):
            with Step1.start(task_id, debug=False) as exec_ctx:
                pass

        with pytest.raises(TaskAlreadySucceedError):
            with Step1.start(task_id, detailed_error=True, debug=False) as exec_ctx:
                pass

        # ----------------------------------------------------------------------
        # run Step 2, it will fail first time
        # ----------------------------------------------------------------------
        step2 = Step2.get_one_or_none(task_id=task_id)
        assert step2.is_pending()
        assert step2.is_locked() is False

        utc_now = get_utc_now()

        with pytest.raises(UserError):
            with Step2.start(task_id, debug=False) as exec_ctx:
                exec_ctx.set_data({"version": 2})
                raise UserError("something is wrong!")

        # check the in-memory updated task
        # check if the task status became "failed"
        assert exec_ctx.task.is_failed()
        # check if the task update time got updated
        assert exec_ctx.task.update_time > utc_now
        # check if the task is locked
        assert exec_ctx.task.is_locked() is False
        # check if the task data is NOT got updated when failed
        assert exec_ctx.task.data == {"version": 1}
        # check if the task retry count is 1
        assert exec_ctx.task.retry == 1
        # check if the task errors got logged
        assert len(exec_ctx.task.errors["history"]) == 1
        assert "UserError" in exec_ctx.task.errors["history"][0]["error"]

        # check the database side updated task
        step2 = Step2.get_one_or_none(task_id=task_id)
        # check if the task status became "failed"
        assert step2.is_failed()
        # check if the task update time got updated
        assert step2.update_time > utc_now
        # check if the task is locked
        assert step2.is_locked() is False
        # check if the task data is NOT got updated when failed
        assert step2.data == {"version": 1}
        # check if the task retry count is 1
        assert step2.retry == 1
        # check if the task errors got logged
        assert len(step2.errors["history"]) == 1
        assert "UserError" in step2.errors["history"][0]["error"]

        # ----------------------------------------------------------------------
        # run Step 2 again, it will succeeded this time
        # ----------------------------------------------------------------------
        utc_now = get_utc_now()

        with Step2.start(task_id, debug=False) as exec_ctx:
            exec_ctx.set_data({"version": 2})

        # check the in-memory updated task
        # check if the task status became "failed"
        assert exec_ctx.task.is_succeeded()
        # check if the task update time got updated
        assert exec_ctx.task.update_time > utc_now
        # check if the task is locked
        assert exec_ctx.task.is_locked() is False
        # check if the task data got updated
        assert exec_ctx.task.data == {"version": 2}
        # check if the task retry count got reset
        assert exec_ctx.task.retry == 0
        # check if the task errors got logged
        assert len(exec_ctx.task.errors["history"]) == 1
        assert "UserError" in exec_ctx.task.errors["history"][0]["error"]

        # check the database side updated task
        step2 = Step2.get_one_or_none(task_id=task_id)
        # check if the task status became "failed"
        assert step2.is_succeeded()
        # check if the task update time got updated
        assert step2.update_time > utc_now
        # check if the task is locked
        assert step2.is_locked() is False
        # check if the task data got updated
        assert step2.data == {"version": 2}
        # check if the task retry count got reset
        assert step2.retry == 0
        # check if the task errors got logged
        assert len(step2.errors["history"]) == 1
        assert "UserError" in step2.errors["history"][0]["error"]

    def _test_2_lock_mechanism(self):
        task_id = "t-2"

        # create a new task
        step1 = Step1.make_and_save(task_id=task_id, data={"version": 0})

        exec_ctx: ExecutionContext
        exec_ctx_1: ExecutionContext
        with Step1.start(task_id, debug=False) as exec_ctx:
            # another worker is trying to start the same task
            with pytest.raises(TaskExecutionError):
                with Step1.start(task_id, debug=False) as exec_ctx_1:
                    pass

            with pytest.raises(TaskIsNotReadyToStartError):
                with Step1.start(task_id, debug=False) as exec_ctx_1:
                    pass

            # show detailed error
            with pytest.raises(TaskLockedError):
                with Step1.start(
                    task_id,
                    detailed_error=True,
                    debug=False,
                ) as exec_ctx_1:
                    pass

            # check the database side updated task
            utc_now_1 = get_utc_now()
            step1 = Step1.get_one_or_none(task_id=task_id)
            # check if the task status is "in_progress",
            # because another worker is working on it
            assert step1.is_in_progress()
            # check if the task update time is updated by the previous worker, not by the current worker
            assert step1.update_time < utc_now_1
            # check if the task is locked
            assert step1.is_locked() is True
            # check if the task retry count is not changed
            assert step1.retry == 0
            # check if the task errors got logged, we don't log error when failed to get lock
            assert len(step1.errors["history"]) == 0

    def _test_3_retry_and_ignore(self):
        task_id = "t-3"

        # create a new tracker
        step1 = Step1.make_and_save(task_id=task_id, data={"version": 0})

        # ----------------------------------------------------------------------
        # run Step 1 three times, and all of them failed, and it reaches ignored status
        # ----------------------------------------------------------------------
        utc_now = get_utc_now()
        exec_ctx: ExecutionContext
        with pytest.raises(UserError):
            with Step1.start(task_id, debug=False) as exec_ctx:
                raise UserError

        with pytest.raises(UserError):
            with Step1.start(task_id, debug=False) as exec_ctx:
                raise UserError

        with pytest.raises(UserError):
            with Step1.start(task_id, debug=False) as exec_ctx:
                raise UserError
        # check the in-memory updated task
        # check if the task status became "ignored"
        assert exec_ctx.task.is_ignored()
        # check if the task update time got updated
        assert exec_ctx.task.update_time > utc_now
        # check if the task is locked
        assert exec_ctx.task.is_locked() is False
        # check if the task retry count got updated
        assert exec_ctx.task.retry == 3
        # check if the task errors got logged
        assert len(exec_ctx.task.errors["history"]) == 3
        for dct in exec_ctx.task.errors["history"]:
            assert "UserError" in dct["error"]

        # check the database side updated task
        step1 = Step1.get_one_or_none(task_id=task_id)
        # check if the task status became "ignored"
        assert step1.is_ignored()
        # check if the task update time got updated
        assert step1.update_time > utc_now
        # check if the task is locked
        assert step1.is_locked() is False
        # check if the task retry count got updated
        assert step1.retry == 3
        # check if the task errors got logged
        assert len(step1.errors["history"]) == 3
        for dct in step1.errors["history"]:
            assert "UserError" in dct["error"]

        # ----------------------------------------------------------------------
        # run Step 1 another time
        # ----------------------------------------------------------------------
        with pytest.raises(TaskExecutionError):
            with Step1.start(task_id, debug=False) as exec_ctx:
                pass

        with pytest.raises(TaskIsNotReadyToStartError):
            with Step1.start(task_id, debug=False) as exec_ctx:
                pass

        with pytest.raises(TaskIgnoredError):
            with Step1.start(task_id, detailed_error=True, debug=False) as exec_ctx:
                pass

    def _test_4(self):
        task_id = "t-4"

        with pytest.raises(TaskIsNotInitializedError):
            with Step1.start(task_id, detailed_error=True, debug=False) as exec_ctx:
                pass

    def _test_11_query_by_status(self):
        # prepare data
        Step1.delete_all()
        with Step1.batch_write() as batch:
            for ith, status_enum in enumerate(Step1StatusEnum, start=1):
                batch.save(
                    Step1.make(
                        task_id=f"t-{ith}",
                        _status=status_enum.value,
                        data={"value": 1},
                    )
                )
        time.sleep(1)

        # each status code only has one item
        for ith, status_enum in enumerate(Step1StatusEnum, start=1):
            res = list(Step1.query_by_status(status=status_enum.value))
            assert len(res) == 1
            assert res[0].task_id == f"t-{ith}"
            break

        res = Step1.query_for_unfinished().all()
        assert len(res) == 2
        assert res[0].task_id == f"t-1"
        assert res[1].task_id == f"t-3"

        # verify that the status index is NOT ALL projection
        step1 = res[0]
        assert step1.data == {}
        step1.refresh()
        assert step1.data == {"value": 1}

        # test the auto_refresh arg
        res = Step1.query_for_unfinished(auto_refresh=True).all()
        assert len(res) == 2
        for task in res:
            assert task.data == {"value": 1}

        # verify the status index object cache
        task._get_status_index(_is_test=True)  # it should not print anything
        task._get_status_index(_is_test=True)  # it should not print anything

        assert Step1.count_tasks_by_use_case_id() == 5
        Step1.delete_tasks_by_use_case_id()
        time.sleep(1)
        assert Step1.count_tasks_by_use_case_id() == 0


class TestStatusTrackerV2UseMock(Base):
    use_mock = True


@pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
class TestStatusTrackerV2UseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.status_tracker", preview=False)
