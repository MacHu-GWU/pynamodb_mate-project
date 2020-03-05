# -*- coding: utf-8 -*-

import os

import pytest
from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

from pynamodb_mate.encrypt_attribute import (
    EncryptUnicodeAttribute,
    EncryptBinaryAttribute,
    EncryptedNumberAttribute,
    EncryptedJsonAttribute,
)

AWS_PROFILE = "pynamodb_mate"
os.environ["AWS_DEFAULT_PROFILE"] = AWS_PROFILE

PASSWORD = "my-password"


class ArchiveModel(Model):
    class Meta:
        table_name = "pynamodb_mate-archive"
        region = "us-east-1"

    aid = UnicodeAttribute(hash_key=True)
    secret_message = EncryptUnicodeAttribute()
    secret_message.encrypt_key = PASSWORD

    secret_binary = EncryptBinaryAttribute()
    secret_binary.encrypt_key = PASSWORD

    secret_integer = EncryptedNumberAttribute()
    secret_integer.encrypt_key = PASSWORD

    secret_float = EncryptedNumberAttribute()
    secret_float.encrypt_key = PASSWORD

    secret_data = EncryptedJsonAttribute()
    secret_data.encrypt_key = PASSWORD


def setup_module(object):
    ArchiveModel.create_table(read_capacity_units=5, write_capacity_units=5)


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


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
