# -*- coding: utf-8 -*-

import pytest
import pynamodb_mate
from pynamodb_mate.tests import py_ver


class OrderModel(pynamodb_mate.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-orders-{py_ver}"
        region = "us-east-1"
        billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

    order_id = pynamodb_mate.UnicodeAttribute(hash_key=True)
    items = pynamodb_mate.CompressedJSONAttribute()


def setup_module(module):
    OrderModel.create_table(wait=True)


order_id = "order_001"
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


def test_io():
    order = OrderModel(
        order_id=order_id,
        items=items,
    )
    order.save()

    order = OrderModel.get(order_id)
    assert order.items == items


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
