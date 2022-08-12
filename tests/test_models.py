# -*- coding: utf-8 -*-

import pytest
from datetime import datetime, timezone
import botocore.session
import pynamodb_mate as pm
from pynamodb_mate.tests import py_ver, BUCKET_NAME
from pynamodb_mate.helpers import remove_s3_prefix

boto_ses = botocore.session.get_session()
s3_client = boto_ses.create_client("s3")


class Model1(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-model1-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    hash_key = pm.UnicodeAttribute(hash_key=True)


class Model2(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-model2-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    hash_key = pm.UnicodeAttribute(hash_key=True)
    range_key = pm.UTCDateTimeAttribute(range_key=True)


def setup_module(module):
    Model1.create_table(wait=True)
    Model2.create_table(wait=True)


class TestModel:
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
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
