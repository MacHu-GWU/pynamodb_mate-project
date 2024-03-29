# -*- coding: utf-8 -*-

import time

from pynamodb_mate.tests import py_ver, BaseTest
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


class TestCache(BaseTest):
    def run_cache_test_case(self, cache: AbstractCache, key: str, value):
        assert cache.get(key) is None
        cache.set(key, value)
        time.sleep(1)
        assert cache.get(key) == value

        cache.set(key, value, expire=3)
        time.sleep(1)
        assert cache.get(key) == value
        time.sleep(5)
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
                JsonDictDynamodbCache(table_name=f"pynamodb-mate-test-cache-{py_ver}"),
                "JsonDictDynamodbCache",
                {"a": 1},
            ),
            (
                JsonListDynamodbCache(table_name=f"pynamodb-mate-test-cache-{py_ver}"),
                "JsonListDynamodbCache",
                [1, 2, 3],
            ),
            (
                JsonDictMultiLayerCache(
                    [
                        JsonDictInMemoryCache(),
                        JsonDictDynamodbCache(
                            table_name=f"pynamodb-mate-test-cache-{py_ver}"
                        ),
                    ]
                ),
                "JsonDictMultiLayerCache",
                {"a": 1},
            ),
            (
                JsonListMultiLayerCache(
                    [
                        JsonListInMemoryCache(),
                        JsonListDynamodbCache(
                            table_name=f"pynamodb-mate-test-cache-{py_ver}"
                        ),
                    ]
                ),
                "JsonListMultiLayerCache",
                [1, 2, 3],
            ),
        ]
        for cache, key, value in args:
            self.run_cache_test_case(cache, key, value)


if __name__ == "__main__":
    from pynamodb_mate.tests import run_cov_test

    run_cov_test(__file__, "pynamodb_mate.patterns.cache", preview=False)
