# -*- coding: utf-8 -*-

import time
import dataclasses

import pytest

from pynamodb.models import PAY_PER_REQUEST_BILLING_MODE
from pynamodb_mate.tests import py_ver, BaseTest
from pynamodb_mate.patterns.status_tracker import (
    BaseStatusEnum,
    StatusAndUpdateTimeIndex,
    BaseStatusTracker,
    TaskLockedError,
    TaskIgnoredError,
    BaseData,
    BaseErrors,
)
from pynamodb_mate.patterns.status_tracker.impl import (
    EPOCH,
    utc_now,
)


@dataclasses.dataclass
class Data(BaseData):
    name: str = dataclasses.field()


class StatusEnum(BaseStatusEnum):
    s00_todo = 0
    s03_in_progress = 3
    s06_failed = 6
    s09_success = 9
    s10_ignore = 10


class UserError(Exception):
    pass


class Tracker(BaseStatusTracker):
    class Meta:
        table_name = f"pynamodb-mate-test-status-tracker-{py_ver}"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    status_and_update_time_index = StatusAndUpdateTimeIndex()

    STATUS_ENUM = StatusEnum

    def start_job(
        self,
        debug=True,
    ) -> "Tracker":
        """
        This is just an example of how to use :meth:`BaseStatusTracker.start`.

        A job should always have four related status codes:

        - in process status
        - failed status
        - success status
        - ignore status

        If you have multiple type of jobs, I recommend creating multiple
        wrapper functions like this for each type of jobs. And ensure that
        the "ignore" status value is the largest status value among all,
        and use the same "ignore" status value for all type of jobs.
        """

        return self.start(
            in_process_status=StatusEnum.s03_in_progress.value,
            failed_status=StatusEnum.s06_failed.value,
            success_status=StatusEnum.s09_success.value,
            ignore_status=StatusEnum.s10_ignore.value,
            debug=debug,
        )


class JobTestTracker(Tracker):
    JOB_ID = "test"


class JobIndexTracker(Tracker):
    JOB_ID = "index"


class TestBaseDataClass:
    def test(self):
        data = Data.from_dict({"name": "Alice"})
        assert data.name == "Alice"
        assert data.to_dict() == {"name": "Alice"}


class TestStatusEnum:
    def test(self):
        assert StatusEnum.s00_todo.status_name == "s00_todo"
        assert StatusEnum.from_value(0) == StatusEnum.s00_todo
        assert StatusEnum.value_to_name(0) == "s00_todo"
        assert StatusEnum.values() == [
            StatusEnum.s00_todo,
            StatusEnum.s03_in_progress,
            StatusEnum.s06_failed,
            StatusEnum.s09_success,
            StatusEnum.s10_ignore,
        ]


class TestStatusTracker(BaseTest):
    @classmethod
    def setup_class(cls):
        print("")
        cls.mock_start()

        Tracker.create_table(wait=True)
        Tracker.delete_all()
        print(f"preview items: {Tracker.get_table_items_console_url()}")

    def test(self):
        self._test_update_context()

        # self._test_1_happy_path()
        # self._test_2_lock_mechanism()
        # self._test_3_retry_and_ignore()

        self._test_11_query_by_status()

    def _test_update_context(self):
        Tracker = JobTestTracker
        task_id = "t-0"
        tracker = Tracker.new(task_id, save=False)
        assert tracker.is_item_exists() is False
        assert tracker.status == StatusEnum.s00_todo.value
        assert tracker.status_name == "s00_todo"

        tracker = Tracker.new(task_id)
        assert tracker.is_item_exists() is True

        assert tracker.job_id == JobTestTracker.JOB_ID
        assert tracker.task_id == task_id
        assert tracker.status == StatusEnum.s00_todo.value
        assert tracker.retry == 0
        assert (utc_now() - tracker.update_time).total_seconds() < 1
        assert tracker.lock is None
        assert tracker.lock_time == EPOCH
        assert tracker.data == {}
        assert tracker.errors == {}

        with tracker.update_context():
            tracker.set_status(status=StatusEnum.s03_in_progress.value)
            tracker.set_retry_plus_one()
            tracker.set_data({"version": 1})
            tracker.set_errors({"error": "something is wrong"})

        assert tracker.status == StatusEnum.s03_in_progress.value
        assert tracker.retry == 1
        assert tracker.data == {"version": 1}
        assert tracker.errors == {"error": "something is wrong"}

        tracker.refresh()
        assert tracker.status == StatusEnum.s03_in_progress.value
        assert tracker.retry == 1
        assert tracker.data == {"version": 1}
        assert tracker.errors == {"error": "something is wrong"}

        with pytest.raises(UserError):
            with tracker.update_context():
                tracker.set_data({"version": 2})
                raise UserError

        # when update fail, the attribute value will not be updated
        assert tracker.data == {"version": 1}

    def _test_1_happy_path(self):
        Tracker = JobTestTracker
        task_id = "t-1"

        # create a new tracker
        tracker = Tracker.new(task_id, data={"version": 1})
        assert tracker.status == StatusEnum.s00_todo.value

        # start the job, this time it will succeed
        with tracker.start_job(debug=True):
            # check if the job status became "in progress"
            assert tracker.status == StatusEnum.s03_in_progress.value
            tracker.refresh()
            assert tracker.status == StatusEnum.s03_in_progress.value

            # do some work
            tracker.set_data({"version": 2})

        # check if the job status become "success"
        assert tracker.status == StatusEnum.s09_success.value
        assert tracker.data == {"version": 2}
        assert tracker.retry == 0
        tracker.refresh()
        assert tracker.status == StatusEnum.s09_success.value
        assert tracker.data == {"version": 2}
        assert tracker.retry == 0

        # start another job, this time it will fail
        tracker = Tracker.new(task_id, data={"version": 1})
        try:
            with tracker.start_job(debug=True):
                tracker.set_data({"version": 2})
                raise UserError("something is wrong!")
        except UserError:
            pass

        assert tracker.status == StatusEnum.s06_failed.value
        assert tracker.data == {"version": 1}  # it is clean data
        assert tracker.retry == 1

        time.sleep(1)
        tracker.refresh()
        assert tracker.status == StatusEnum.s06_failed.value
        assert tracker.data == {"version": 1}  # it is the database side data
        assert tracker.retry == 1

    def _test_2_lock_mechanism(self):
        Tracker = JobTestTracker
        task_id = "t-2"

        # create a new tracker
        tracker = Tracker.new(task_id)
        assert tracker.status == StatusEnum.s00_todo.value
        assert tracker.lock is None
        assert tracker.is_locked() is False

        time.sleep(1)
        tracker = Tracker.get_one_or_none(task_id)
        assert tracker.status == StatusEnum.s00_todo.value
        assert tracker.lock is None
        assert tracker.is_locked() is False

        # lock it
        with tracker.update_context():
            tracker.set_locked()

        # verify it is really locked
        assert tracker.lock is not None
        assert tracker.is_locked() is True

        # run a job while it is locked
        assert tracker.data == {}

        with pytest.raises(TaskLockedError):
            with tracker.start_job():
                tracker.set_data({"version": 2})

        # nothing should happen
        # data is not changed
        time.sleep(1)
        assert tracker.is_locked() is True
        assert tracker.data == {}

        # status and update_time is not changed
        update_time = tracker.update_time
        tracker.refresh()
        assert tracker.update_time == update_time

    def _test_3_retry_and_ignore(self):
        Tracker = JobTestTracker
        task_id = "t-3"

        # create a new tracker
        tracker = Tracker.new(task_id, data={"version": 1})
        assert tracker.retry == 0

        # 1st try
        with pytest.raises(UserError):
            with tracker.start_job():
                raise UserError

        assert tracker.retry == 1
        assert tracker.status == StatusEnum.s06_failed.value
        tracker.refresh()
        assert tracker.retry == 1
        assert tracker.status == StatusEnum.s06_failed.value

        # 2nd try
        with pytest.raises(UserError):
            with tracker.start_job():
                raise UserError

        assert tracker.retry == 2
        assert tracker.status == StatusEnum.s06_failed.value
        tracker.refresh()
        assert tracker.retry == 2
        assert tracker.status == StatusEnum.s06_failed.value

        # 3rd try success, the retry reset to 0
        with tracker.start_job():
            tracker.set_data({"version": 2})
        assert tracker.retry == 0
        assert tracker.status == StatusEnum.s09_success.value
        assert tracker.data == {"version": 2}
        tracker.refresh()
        assert tracker.retry == 0
        assert tracker.status == StatusEnum.s09_success.value
        assert tracker.data == {"version": 2}

        # make three attempts to fail
        for _ in range(Tracker.MAX_RETRY):
            with pytest.raises(UserError):
                with tracker.start_job():
                    raise UserError

        assert tracker.retry == Tracker.MAX_RETRY
        assert tracker.status == StatusEnum.s10_ignore.value
        tracker.refresh()
        assert tracker.retry == Tracker.MAX_RETRY
        assert tracker.status == StatusEnum.s10_ignore.value

        with pytest.raises(TaskIgnoredError):
            with tracker.start_job():
                tracker.set_data({"version": 3})

        assert tracker.retry == Tracker.MAX_RETRY
        assert tracker.status == StatusEnum.s10_ignore.value
        assert tracker.data == {"version": 2}
        tracker.refresh()
        assert tracker.retry == Tracker.MAX_RETRY
        assert tracker.status == StatusEnum.s10_ignore.value
        assert tracker.data == {"version": 2}

    def _test_11_query_by_status(self):
        Tracker = JobIndexTracker

        # prepare data
        with Tracker.batch_write() as batch:
            batch.save(
                Tracker.make("t-1", status=StatusEnum.s00_todo.value, data={"value": 1})
            )
            batch.save(
                Tracker.make(
                    "t-2", status=StatusEnum.s03_in_progress.value, data={"value": 1}
                )
            )
            batch.save(
                Tracker.make(
                    "t-3", status=StatusEnum.s06_failed.value, data={"value": 1}
                )
            )
            batch.save(
                Tracker.make(
                    "t-4", status=StatusEnum.s09_success.value, data={"value": 1}
                )
            )
            batch.save(
                Tracker.make(
                    "t-5", status=StatusEnum.s10_ignore.value, data={"value": 1}
                )
            )

        time.sleep(3)

        # each status code only has one item
        for ith, status in enumerate(StatusEnum, start=1):
            res = list(Tracker.query_by_status(status.value))
            assert len(res) == 1
            assert res[0].task_id == f"t-{ith}"

        res = Tracker.query_by_status(
            [
                StatusEnum.s00_todo.value,
                StatusEnum.s06_failed.value,
            ]
        ).all()
        assert len(res) == 2
        assert res[0].task_id == f"t-1"
        assert res[1].task_id == f"t-3"

        # verify that the status index is NOT ALL projection
        tracker = res[0]
        assert tracker.data == {}
        tracker.refresh()
        assert tracker.data == {"value": 1}

        # test the auto_refresh arg
        res = Tracker.query_by_status(
            [
                StatusEnum.s00_todo,
                StatusEnum.s06_failed.value,
            ],
            auto_refresh=True,
        ).all()
        assert len(res) == 2

        for tracker in res:
            assert tracker.data == {"value": 1}

        # verify the status index object cache
        Tracker._get_status_index()  # it should not print anything
        Tracker._get_status_index()  # it should not print anything

        assert Tracker.count_items_by_job_id() == 5
        Tracker.delete_all_by_job_id()
        time.sleep(1)
        assert Tracker.count_items_by_job_id() == 0


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.status_tracker", preview=False)
