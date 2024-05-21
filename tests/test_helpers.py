# -*- coding: utf-8 -*-

from pynamodb_mate import helpers


def test_bytes_to_base64str():
    b = "Hello".encode("utf-8")
    s = helpers.bytes_to_base85str(b)
    assert isinstance(s, str)
    assert helpers.base85str_to_bytes(s) == b


def test_hash():
    b = "Hello".encode("utf-8")
    helpers.sha256(b)


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.helpers", preview=False)
