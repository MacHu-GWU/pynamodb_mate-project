# -*- coding: utf-8 -*-

import pytest
import time

from pynamodb_mate.tests.constants import PY_VER, PYNAMODB_VER, IS_CI
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
    json_dict_dynamodb_cache = JsonDictDynamodbCache(
        table_name=f"pynamodb-mate-test-cache-{PY_VER}-{PYNAMODB_VER}",
        create=False,
    )
    json_list_dynamodb_cache = JsonListDynamodbCache(
        table_name=f"pynamodb-mate-test-cache-{PY_VER}-{PYNAMODB_VER}",
        create=False,
    )
    model_list = [
        json_dict_dynamodb_cache.Table,
        json_list_dynamodb_cache.Table,
    ]

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


@pytest.mark.skipif(IS_CI, reason="Skip test that requires AWS resources in CI.")
class TestCacheUseAws(Base):
    use_mock = False


if __name__ == "__main__":
    from pynamodb_mate.tests.helper import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.cache", preview=False)
