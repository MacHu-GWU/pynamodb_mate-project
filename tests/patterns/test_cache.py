# -*- coding: utf-8 -*-

import pytest
import time

from boto_session_manager import BotoSesManager
from pynamodb_mate.tests.constants import py_ver, pynamodb_ver, aws_profile, is_ci
from pynamodb_mate.tests.base_test import BaseTest
from pynamodb_mate.patterns.cache.abstract import AbstractCache
from pynamodb_mate.patterns.cache.backend.in_memory import (
    JsonDictInMemoryCache,
    JsonListInMemoryCache,
)
from pynamodb_mate.patterns.cache.backend.dynamodb import (
    JsonDictDynamodbCache,
    JsonListDynamodbCache,
)
from pynamodb_mate.patterns.cache.multi_layer import (
    JsonDictMultiLayerCache,
    JsonListMultiLayerCache,
)


class TestInMemoryCache:
    def test(self):
        cache = JsonDictInMemoryCache()

        cache.set("k1", {"a": 1})
        cache.set("k2", {"a": 2}, expire=1)

        assert len(cache._cache) == 2

        time.sleep(3)
        cache.clear_expired()
        assert len(cache._cache) == 1

        cache.clear_all()
        assert len(cache._cache) == 0


class Base(BaseTest):

    @classmethod
    def setup_class_post_hook(cls):
        cls.json_dict_dynamodb_cache = JsonDictDynamodbCache(
            table_name=f"pynamodb-mate-test-cache-{py_ver}-{pynamodb_ver}",
            create=False,
        )
        cls.json_list_dynamodb_cache = JsonListDynamodbCache(
            table_name=f"pynamodb-mate-test-cache-{py_ver}-{pynamodb_ver}",
            create=False,
        )
        cls.json_dict_dynamodb_cache.Table._connection = None
        cls.json_list_dynamodb_cache.Table._connection = None
        # clean up the table connection cache so that pynamodb can find the right boto3 session
        if cls.use_mock:
            cls.json_dict_dynamodb_cache.Table.create_table(wait=True)
            cls.json_list_dynamodb_cache.Table.create_table(wait=True)
        else:
            with BotoSesManager(profile_name=aws_profile).awscli():
                cls.json_dict_dynamodb_cache.Table.create_table(wait=True)
                cls.json_list_dynamodb_cache.Table.create_table(wait=True)
                cls.json_dict_dynamodb_cache.Table.delete_all()
                cls.json_list_dynamodb_cache.Table.delete_all()

    def run_cache_test_case(self, cache: AbstractCache, key: str, value):
        # print(f"Testing the {key!r} cache ...") # for debug only
        assert cache.get(key) is None
        cache.set(key, value)
        time.sleep(0.1)
        assert cache.get(key) == value

        cache.set(key, value, expire=1)
        time.sleep(0.5)
        assert cache.get(key) == value
        time.sleep(0.5)
        assert cache.get(key) is None

    def test_cache(self):
        args = [
            (
                JsonDictInMemoryCache(),
                "JsonDictInMemoryCache",
                {"a": 1},
            ),
            (
                JsonListInMemoryCache(),
                "JsonListInMemoryCache",
                [1, 2, 3],
            ),
            (
                self.json_dict_dynamodb_cache,
                "JsonDictDynamodbCache",
                {"a": 1},
            ),
            (
                self.json_list_dynamodb_cache,
                "JsonListDynamodbCache",
                [1, 2, 3],
            ),
            (
                JsonDictMultiLayerCache(
                    [
                        JsonDictInMemoryCache(),
                        self.json_dict_dynamodb_cache,
                    ]
                ),
                "JsonDictMultiLayerCache",
                {"a": 1},
            ),
            (
                JsonListMultiLayerCache(
                    [
                        JsonListInMemoryCache(),
                        self.json_list_dynamodb_cache,
                    ]
                ),
                "JsonListMultiLayerCache",
                [1, 2, 3],
            ),
        ]
        for cache, key, value in args:
            self.run_cache_test_case(cache, key, value)


class TestCacheUseMock(Base):
    use_mock = True


@pytest.mark.skipif(is_ci, reason="Skip test that requires AWS resources in CI.")
class TestCacheUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.cache", preview=False)
