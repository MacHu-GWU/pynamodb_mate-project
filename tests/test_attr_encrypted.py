# -*- coding: utf-8 -*-

import pytest
import pynamodb_mate
from pynamodb_mate.tests import py_ver

ENCRYPTION_KEY = "my-password"


class ArchiveModel(pynamodb_mate.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-archive-{py_ver}"
        region = "us-east-1"
        billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

    aid = pynamodb_mate.UnicodeAttribute(hash_key=True)
    secret_message = pynamodb_mate.EncryptUnicodeAttribute()
    secret_message.encryption_key = ENCRYPTION_KEY
    secret_message.determinative = True

    secret_binary = pynamodb_mate.EncryptBinaryAttribute()
    secret_binary.encryption_key = ENCRYPTION_KEY
    secret_binary.determinative = False

    secret_integer = pynamodb_mate.EncryptedNumberAttribute()
    secret_integer.encryption_key = ENCRYPTION_KEY
    secret_integer.determinative = True

    secret_float = pynamodb_mate.EncryptedNumberAttribute()
    secret_float.encryption_key = ENCRYPTION_KEY
    secret_float.determinative = False

    secret_data = pynamodb_mate.EncryptedJsonAttribute()
    secret_data.encryption_key = ENCRYPTION_KEY
    secret_data.determinative = False


def setup_module(module):
    ArchiveModel.create_table(wait=True)


def count_result(result):
    for i in result:
        pass
    return result.total_count


class TestEncryptUnicode(object):
    def test(self):
        # Test encryption / decryption
        msg = "attack at 2PM tomorrow!"
        binary = "a secret image".encode("utf-8")
        data = {"Alice": 1, "Bob": 2, "Cathy": 3}
        model = ArchiveModel(
            aid="aid-001",
            secret_message=msg,
            secret_binary=binary,
            secret_integer=1234,
            secret_float=3.14,
            secret_data=data,
        )
        model.save()

        model = ArchiveModel.get("aid-001")
        assert model.secret_message == msg
        assert model.secret_binary == binary
        assert model.secret_integer == 1234
        assert model.secret_float == pytest.approx(3.14)
        assert model.secret_data == data

        # equal filter on encrypted field
        assert count_result(
            ArchiveModel.scan(ArchiveModel.secret_message == msg)
        ) == 1
        assert count_result(
            ArchiveModel.scan(ArchiveModel.secret_message == "hold the fire now!")
        ) == 0

        # for non-determinative field, same input and same output
        # doesn't return same output
        assert count_result(
            ArchiveModel.scan(ArchiveModel.secret_binary == binary)
        ) == 0


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
