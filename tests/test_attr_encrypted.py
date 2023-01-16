# -*- coding: utf-8 -*-

import pytest
import pynamodb_mate as pm
from pynamodb_mate.tests import py_ver, BaseTest

ENCRYPTION_KEY = "my-password"


class ArchiveModel(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-archive-{py_ver}"
        region = "us-east-1"
        billing_mode = pm.PAY_PER_REQUEST_BILLING_MODE

    aid = pm.UnicodeAttribute(hash_key=True)
    secret_message = pm.EncryptedUnicodeAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=True,
    )

    secret_binary = pm.EncryptedBinaryAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=False,
    )

    secret_integer = pm.EncryptedNumberAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=True,
    )

    secret_float = pm.EncryptedNumberAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=False,
    )

    secret_data = pm.EncryptedJsonDictAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=False,
    )


def count_result(result):
    for i in result:
        pass
    return result.total_count


class TestEncryptUnicode(BaseTest):
    @classmethod
    def setup_class(cls):
        cls.mock_start()
        ArchiveModel.create_table(wait=True)

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
        assert count_result(ArchiveModel.scan(ArchiveModel.secret_message == msg)) == 1
        assert (
            count_result(
                ArchiveModel.scan(ArchiveModel.secret_message == "hold the fire now!")
            )
            == 0
        )

        # for non-determinative field, same input and same output
        # doesn't return same output
        assert (
            count_result(ArchiveModel.scan(ArchiveModel.secret_binary == binary)) == 0
        )


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.encrypted", preview=False)
