# -*- coding: utf-8 -*-

import pytest


def test():
    import pynamodb_mate

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
    _ = pynamodb_mate.EncryptUnicodeAttribute
    _ = pynamodb_mate.EncryptBinaryAttribute
    _ = pynamodb_mate.EncryptedJsonAttribute
    _ = pynamodb_mate.S3BackedBigBinaryAttribute
    _ = pynamodb_mate.S3BackedBigTextAttribute


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
