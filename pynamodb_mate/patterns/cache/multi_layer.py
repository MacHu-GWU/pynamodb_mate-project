# -*- coding: utf-8 -*-

"""

"""

import typing as T
from .abstract import AbstractCache

VALUE = T.TypeVar("VALUE")


class MultiLayerCache(T.Generic[VALUE]):
    """
    Combine multiple cache backend together.

    For example, you could define a cache that prefer to use in-memory cache,
    then dynamodb cache.

    - Set value logic: update in-memory cache, then dynamodb cache
    - Get value logic: try to get value from in-memory cache, if not hit,
        then try dynamodb cache.
    """

    def __init__(self, cache_list: T.List[AbstractCache]):
        self.cache_list = cache_list

    def set(
        self,
        key: str,
        value: VALUE,
        expire: int = 0,
    ):
        for cache in self.cache_list:
            cache.set(key, value, expire)

    def get(
        self,
        key: str,
    ) -> VALUE:
        for cache in self.cache_list:
            val = cache.get(key)
            if val is not None:
                return val
        return None


class JsonDictMultiLayerCache(MultiLayerCache[dict]):
    pass


class JsonListMultiLayerCache(MultiLayerCache[list]):
    pass
