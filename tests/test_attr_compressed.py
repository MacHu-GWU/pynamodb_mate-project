# -*- coding: utf-8 -*-

import pytest

from boto_session_manager import BotoSesManager
import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import py_ver, pynamodb_ver, aws_profile, is_ci
from pynamodb_mate.tests.base_test import BaseTest


# Define the Data Model to use compressed attribute
class OrderModel(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-orders-{py_ver}-{pynamodb_ver}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    # fmt: off
    order_id: pm.REQUIRED_STR = pm.UnicodeAttribute(hash_key=True)
    # original value is unicode str
    description: pm.OPTIONAL_BINARY = pm.attributes.CompressedUnicodeAttribute(null=True)
    # original value is binary bytes
    image: pm.OPTIONAL_BINARY = pm.attributes.CompressedBinaryAttribute(null=True)
    # original value is any json serializable object
    items: pm.OPTIONAL_BINARY = pm.attributes.CompressedJSONDictAttribute(null=True)
    # fmt: on


class Base(BaseTest):
    @classmethod
    def setup_class_post_hook(cls):
        # clean up the table connection cache so that pynamodb can find the right boto3 session
        OrderModel._connection = None

        if cls.use_mock:
            OrderModel.create_table(wait=False)
        else:
            with BotoSesManager(profile_name=aws_profile).awscli():
                OrderModel.create_table(wait=True)
                OrderModel.delete_all()

    def test_io_good_case(self):
        # Create an item
        order_id = "order_001"
        description = "a fancy order!" * 10
        image = description.encode("utf-8")
        items = [
            {
                "item_id": "i_001",
                "item_name": "apple",
                "item_price": 2.4,
                "quantity": 8,
            },
            {
                "item_id": "i_002",
                "item_name": "banana",
                "item_price": 0.53,
                "quantity": 5,
            },
        ]
        order = OrderModel(
            order_id=order_id,
            description=description,
            image=image,
            items=items,
        )
        # Save item to Dynamodb
        order.save()

        # Get the value back and verify
        order = OrderModel.get(order_id)
        assert order.description == description
        assert order.image == image
        assert order.items == items

    def test_io_edge_case(self):
        # None value works too.
        order_id = "order_002"
        order = OrderModel(
            order_id=order_id,
            description=None,
            image=None,
            items=None,
        )
        order.save()

        order = OrderModel.get(order_id)
        assert order.description is None
        assert order.image is None
        assert order.items is None


class TestCompressedAttributeUseMock(Base):
    use_mock = True


@pytest.mark.skipif(is_ci, reason="Skip test that requires AWS resources in CI.")
class TestCompressedAttributeUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.compressed")
