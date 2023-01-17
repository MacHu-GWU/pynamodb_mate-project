# -*- coding: utf-8 -*-

from datetime import datetime, timezone

import pynamodb_mate as pm
from pynamodb_mate.tests import py_ver, BaseTest


class Model(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-model-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    hash_key = pm.UnicodeAttribute(hash_key=True)
    data = pm.JSONAttribute(default=lambda: dict())

    def __post_init__(self):
        self.data["a"] = 1


class Model1(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-model1-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    hash_key = pm.UnicodeAttribute(hash_key=True)
    data = pm.JSONAttribute(default=lambda: dict())


class Model2(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-model2-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    hash_key = pm.UnicodeAttribute(hash_key=True)
    range_key = pm.UTCDateTimeAttribute(range_key=True)
    data = pm.JSONAttribute(default=lambda: dict())


class TestModel(BaseTest):
    @classmethod
    def setup_class(cls):
        cls.mock_start()

        Model1.create_table(wait=True)
        Model2.create_table(wait=True)
        Model1.delete_all()
        Model2.delete_all()

    def test_post_init(self):
        model = Model(hash_key="a")
        assert model.data == {"a": 1}

    def test_to_dict(self):
        model = Model1(hash_key="a")

        data1 = model.to_dict(copy=True)
        data2 = model.to_dict(copy=True)
        assert data1 == {"hash_key": "a", "data": {}}
        data1["data"]["a"] = 1
        assert data2["data"] == {}

        data1 = model.to_dict(copy=False)
        data2 = model.to_dict(copy=False)
        assert data1 == {"hash_key": "a", "data": {}}
        data1["data"]["a"] = 1
        assert data2["data"] == {"a": 1}

    def test_get_one_or_none(self):
        model = Model1().get_one_or_none("one-or-none")
        assert model is None
        Model1("one-or-none").save()
        model = Model1().get_one_or_none("one-or-none")
        assert model.to_dict() == {"hash_key": "one-or-none", "data": {}}

        model = Model2().get_one_or_none(
            "one-or-none", datetime(2000, 1, 1, tzinfo=timezone.utc)
        )
        assert model is None
        Model2("one-or-none", datetime(2000, 1, 1, tzinfo=timezone.utc)).save()
        model = Model2().get_one_or_none(
            "one-or-none", datetime(2000, 1, 1, tzinfo=timezone.utc)
        )
        assert model.to_dict() == {
            "hash_key": "one-or-none",
            "range_key": datetime(2000, 1, 1, tzinfo=timezone.utc),
            "data": {},
        }

    def test_iter(self):
        Model1.delete_all()
        with Model1.batch_write() as batch:
            for id in range(1, 1 + 10):
                model = Model1(hash_key=str(id), data={"value": id})
                batch.save(model)

        iterator = Model1.iter_query(hash_key="1")
        assert iterator.one().data == {"value": 1}

        iterator = Model1.iter_scan()
        for item in iterator:
            assert item.hash_key == str(item.data["value"])

    def test_delete_if_exists(self):
        model = Model1(hash_key="delete-if-exists")
        assert model.delete_if_exists() is False
        model.save()
        assert model.delete_if_exists() is True

        model = Model2(
            hash_key="delete-if-exists",
            range_key=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        assert model.delete_if_exists() is False
        model.save()
        assert model.delete_if_exists() is True

    def test_console_url(self):
        Model1.delete_all()
        Model2.delete_all()

        model1 = Model1(
            hash_key="a",
        )
        model1.save()
        _ = Model1.get_table_overview_console_url()
        _ = Model1.get_table_items_console_url()
        _ = model1.item_detail_console_url
        # print(model1.item_detail_console_url)

        model2 = Model2(
            hash_key="a",
            range_key=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        model2.save()
        _ = model2.item_detail_console_url
        # print(model2.item_detail_console_url)


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.models", preview=False)
