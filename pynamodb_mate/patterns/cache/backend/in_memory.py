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
    Base class for in-memory cache backend. You have to implement your own
    ``serialize()`` and ``deserialize()`` methods before use.
    """

    def __init__(self):
        self._cache: T.Dict[str, CacheRecord] = dict()

    def _set_record_to_backend(self, key: str, record: CacheRecord):
        self._cache[key] = record

    def _get_record_from_backend(self, key: str) -> T.Optional[CacheRecord]:
        return self._cache.get(key)

    def clear_all(self):
        self._cache.clear()

    def clear_expired(self):
        now_ts = utc_now().timestamp()

        to_delete = list()
        for key, record in self._cache.items():
            if (
                record.expire != 0
                and (now_ts - record.update_ts) > record.expire
            ):
                to_delete.append(key)

        for key in to_delete:
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
