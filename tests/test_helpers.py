# -*- coding: utf-8 -*-

import pytest
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
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
