# -*- coding: utf-8 -*-

import pytest
from pynamodb_mate.cipher import str_to_key, AesEcbCipher, AesCtrCipher

KEY = str_to_key("mypassword")


class TestAESECBCipher:
    def test(self):
        cipher = AesEcbCipher(KEY)
        b = ("hello" * 1000).encode("utf-8")
        b1 = cipher.encrypt(b)
        b2 = cipher.encrypt(b)
        assert b1 == b2
        assert cipher.decrypt(b1) == b
        assert cipher.decrypt(b2) == b


class TestAESCTRCipher:
    def test(self):
        cipher = AesCtrCipher(KEY)
        b = ("hello" * 1000).encode("utf-8")
        b1 = cipher.encrypt(b)
        b2 = cipher.encrypt(b)
        assert b1 != b2
        assert cipher.decrypt(b1) == b
        assert cipher.decrypt(b2) == b


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.cipher", preview=False)
