# -*- coding: utf-8 -*-

import pytest


def test():
    import pynamodb_mate

    _ = pynamodb_mate.BINARY
    _ = pynamodb_mate.BINARY_SET
    _ = pynamodb_mate.BOOLEAN
    _ = pynamodb_mate.LIST
    _ = pynamodb_mate.MAP
    _ = pynamodb_mate.NULL
    _ = pynamodb_mate.NUMBER
    _ = pynamodb_mate.NUMBER_SET
    _ = pynamodb_mate.STRING
    _ = pynamodb_mate.STRING_SET
    _ = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE
    _ = pynamodb_mate.PROVISIONED_BILLING_MODE

    _ = pynamodb_mate.Model
    _ = pynamodb_mate.UnicodeAttribute
    _ = pynamodb_mate.BinaryAttribute
    _ = pynamodb_mate.NumberAttribute
    _ = pynamodb_mate.BooleanAttribute
    _ = pynamodb_mate.UnicodeSetAttribute
    _ = pynamodb_mate.BinarySetAttribute
    _ = pynamodb_mate.NumberSetAttribute
    _ = pynamodb_mate.ListAttribute
    _ = pynamodb_mate.MapAttribute
    _ = pynamodb_mate.DynamicMapAttribute
    _ = pynamodb_mate.JSONAttribute
    _ = pynamodb_mate.UTCDateTimeAttribute
    _ = pynamodb_mate.EncryptedNumberAttribute
    _ = pynamodb_mate.EncryptedUnicodeAttribute
    _ = pynamodb_mate.EncryptedBinaryAttribute
    _ = pynamodb_mate.EncryptedJsonAttribute
    _ = pynamodb_mate.S3BackedBigBinaryAttribute
    _ = pynamodb_mate.S3BackedBigTextAttribute

    _ = pynamodb_mate.Connection

    _ = pynamodb_mate.GlobalSecondaryIndex
    _ = pynamodb_mate.LocalSecondaryIndex
    _ = pynamodb_mate.KeysOnlyProjection
    _ = pynamodb_mate.IncludeProjection
    _ = pynamodb_mate.AllProjection

    _ = pynamodb_mate.TransactGet
    _ = pynamodb_mate.TransactWrite

    _ = pynamodb_mate.pre_dynamodb_send
    _ = pynamodb_mate.post_dynamodb_send


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
