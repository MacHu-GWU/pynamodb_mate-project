# -*- coding: utf-8 -*-

"""
Implement an abstract cache backend. You can customize your own cache backend.
"""

import typing as T
import dataclasses
from abc import ABC, abstractmethod

from .utils import utc_now

VALUE = T.TypeVar("VALUE")  # represent a cached value, can be any object


@dataclasses.dataclass
class CacheRecord:
    """
    Represent a cache record.

    :param key: the cache key
    :param value: the binary view of the original value
    :param expire: cache expire time, in seconds
    :param update_ts: last update timestamp
    """

    value: bytes
    expire: T.Union[int, float]
    update_ts: T.Union[int, float]

    __slots__ = ("value", "expire", "update_ts")


class AbstractCache(
    ABC,
    T.Generic[VALUE], # the type of the cached value
):
    """
    An abstract cache class regardless of the backend.
    """

    @abstractmethod
    def serialize(self, value: VALUE) -> bytes:
        """
        Abstract serialization function that convert the original value to
        binary data.
        """
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, value: bytes) -> VALUE:
        """
        Abstract deserialization function the recover the original value from
        binary data.
        """
        raise NotImplementedError

    @abstractmethod
    def _set_record_to_backend(self, key: str, record: CacheRecord):
        """
        Store cache record to the backend.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_record_from_backend(self, key: str) -> T.Optional[CacheRecord]:
        """
        Get cache record from backend, if not hit, return None
        """
        raise NotImplementedError

    def clear_all(self):
        """
        Disable all records in cache.
        """
        raise NotImplementedError

    def clear_expired(self):
        """
        Disable all expired records in cache.
        """
        raise NotImplementedError

    def set(
        self,
        key: str,
        value: VALUE,
        expire: int = 0,
    ):
        """
        Store object in cache.

        :param key: cache key.
        :param value: the object you stored in cache.
        :param expire: Time-to-live in seconds.
        """
        record = CacheRecord(
            value=self.serialize(value),
            expire=expire,
            update_ts=utc_now().timestamp(),
        )
        self._set_record_to_backend(key, record)

    def get(
        self,
        key: str,
    ) -> T.Optional[VALUE]:
        """
        Get object from cache.

        :param key: cache key

        :return: the cached object.
        """
        record = self._get_record_from_backend(key)

        if record is None:
            return None

        if record.expire:
            now = utc_now()
            if (now.timestamp() - record.update_ts) < record.expire:
                return self.deserialize(record.value)
            else:
                return None
        else:
            return self.deserialize(record.value)
