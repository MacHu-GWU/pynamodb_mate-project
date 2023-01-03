# -*- coding: utf-8 -*-

# Import pynamodb_mate library
import pynamodb_mate
from pynamodb_mate.tests import py_ver


# Define the Data Model to use compressed attribute
class OrderModel(pynamodb_mate.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-orders-{py_ver}"
        region = "us-east-1"
        billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

    order_id = pynamodb_mate.UnicodeAttribute(hash_key=True)

    # original value is unicode str
    description = pynamodb_mate.CompressedUnicodeAttribute(null=True)

    # original value is binary bytes
    image = pynamodb_mate.CompressedBinaryAttribute(null=True)

    # original value is any json serializable object
    items = pynamodb_mate.CompressedJSONDictAttribute(null=True)


def setup_module(module):
    # Create table if not exists
    OrderModel.create_table(wait=True)


def test_io_good_case():
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


def test_io_edge_case():
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


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.compressed")
