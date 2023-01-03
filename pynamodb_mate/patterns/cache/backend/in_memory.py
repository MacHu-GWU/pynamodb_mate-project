# -*- coding: utf-8 -*-

"""

"""

import typing as T

import json

from ..utils import utc_now
from ..abstract import CacheRecord, AbstractCache


VALUE = T.TypeVar("VALUE")  # represent a cached value, can be any object


class InMemoryBackend(
    AbstractCache,
    T.Generic[VALUE],
):
    """
    Base in memory cache backend. You can customize the behavior by adding
    custom serializer / deserializer.
    """

    def __init__(self):
        self._cache: T.Dict[str, CacheRecord] = dict()

    def _set_record_to_backend(self, key: str, record: CacheRecord):
        self._cache[key] = record

    def _get_record_from_backend(self, key: str) -> T.Optional[CacheRecord]:
        return self._cache.get(key)

    def clear_all(self):
        self._cache.clear()

    def clea_expired(self):
        now_ts = utc_now().timestamp()
        for key, record in self._cache.items():
            if (now_ts - record.update_ts) > record.expire:
                del self._cache[key]


class JsonDictInMemoryCache(
    InMemoryBackend[dict],
):
    """
    A built-in In memory cache designed to store JSON serializable dict.
    """

    def serialize(self, value: dict) -> bytes:
        return json.dumps(value).encode("utf-8")

    def deserialize(self, value: bytes) -> dict:
        return json.loads(value.decode("utf-8"))


class JsonListInMemoryCache(
    InMemoryBackend[list],
):
    """
    A built-in In memory cache designed to store JSON serializable list.
    """

    def serialize(self, value: list) -> bytes:
        return json.dumps(value).encode("utf-8")

    def deserialize(self, value: bytes) -> list:
        return json.loads(value.decode("utf-8"))
