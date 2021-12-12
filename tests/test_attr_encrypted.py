# -*- coding: utf-8 -*-

import pytest
import pynamodb_mate
from pynamodb_mate.tests import py_ver

PASSWORD = "my-password"


class ArchiveModel(pynamodb_mate.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-archive-{py_ver}"
        region = "us-east-1"
        billing_mode = pynamodb_mate.PAY_PER_REQUEST_BILLING_MODE

    aid = pynamodb_mate.UnicodeAttribute(hash_key=True)
    secret_message = pynamodb_mate.EncryptUnicodeAttribute()
    secret_message.encrypt_key = PASSWORD

    secret_binary = pynamodb_mate.EncryptBinaryAttribute()
    secret_binary.encrypt_key = PASSWORD

    secret_integer = pynamodb_mate.EncryptedNumberAttribute()
    secret_integer.encrypt_key = PASSWORD

    secret_float = pynamodb_mate.EncryptedNumberAttribute()
    secret_float.encrypt_key = PASSWORD

    secret_data = pynamodb_mate.EncryptedJsonAttribute()
    secret_data.encrypt_key = PASSWORD


def setup_module(module):
    ArchiveModel.create_table(wait=True)


class TestEncryptUnicode(object):
    def test(self):
        model = ArchiveModel(
            aid="aid-001",
            secret_message="attack at 2PM tomorrow!",
            secret_binary="a secret image".encode("utf-8"),
            secret_integer=1234,
            secret_float=3.14,
            secret_data={"Alice": 1, "Bob": 2, "Cathy": 3},
        )
        model.save()

        model = ArchiveModel.get("aid-001")
        assert model.secret_message == "attack at 2PM tomorrow!"
        assert model.secret_binary.decode("utf-8") == "a secret image"
        assert model.secret_integer == 1234
        assert model.secret_float == 3.14
        assert model.secret_data == {"Alice": 1, "Bob": 2, "Cathy": 3}

        # print(ArchiveModel.scan(ArchiveModel.secret_message == "attack at 2PM tomorrow").total_count)
        # filter_condition = \
        #     ArchiveModel.secret_message == "attack at 2PM tomorrow!"
        # ArchiveModel.aid == "aid-001"
        # print(filter_condition)
        # for model in ArchiveModel.scan(filter_condition):
        #     print(model)

        # print(ArchiveModel.aid == "aid-001")
        # print(ArchiveModel.secret_message == "attack at 2PM tomorrow")


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
