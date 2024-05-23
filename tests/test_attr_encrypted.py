# -*- coding: utf-8 -*-

import pytest

import pynamodb_mate.api as pm
from pynamodb_mate.tests.constants import PY_VER, PYNAMODB_VER, IS_CI
from pynamodb_mate.tests.base_test import BaseTest

ENCRYPTION_KEY = "my-password"


class ArchiveModel(pm.Model):
    class Meta:
        table_name = f"pynamodb-mate-test-archive-{PY_VER}-{PYNAMODB_VER}"
        region = "us-east-1"
        billing_mode = pm.constants.PAY_PER_REQUEST_BILLING_MODE

    aid = pm.UnicodeAttribute(hash_key=True)
    secret_message: pm.REQUIRED_BINARY = pm.attributes.EncryptedUnicodeAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=True,
    )
    secret_binary: pm.REQUIRED_BINARY = pm.attributes.EncryptedBinaryAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=False,
    )
    secret_integer: pm.REQUIRED_BINARY = pm.attributes.EncryptedNumberAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=True,
    )
    secret_float: pm.REQUIRED_BINARY = pm.attributes.EncryptedNumberAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=False,
    )
    secret_data: pm.REQUIRED_BINARY = pm.attributes.EncryptedJsonDictAttribute(
        encryption_key=ENCRYPTION_KEY,
        determinative=False,
    )


def count_result(result):
    for i in result:
        pass
    return result.total_count


class Base(BaseTest):
    model_list = [
        ArchiveModel,
    ]

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


class TestEncryptUseMock(Base):
    use_mock = True


@pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
class TestEncryptUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.attributes.encrypted", preview=False)
