# -*- coding: utf-8 -*-

"""
DynamoDB backend for cache.
"""

import typing as T
import json

from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.attributes import (
    UnicodeAttribute,
    BinaryAttribute,
    NumberAttribute,
)

from ....models import Model
from ..abstract import CacheRecord, AbstractCache


VALUE = T.TypeVar("VALUE")  # represent a cached value, can be any object


class DynamoDBBackend(
    AbstractCache,
    T.Generic[VALUE],
):
    """
    Base class for DynamoDB cache backend. You have to implement your own
    ``serialize()`` and ``deserialize()`` methods before use.

    :param table_name: DynamoDB table name
    :param region: aws region
    :param billing_mode: billing model to use when creating the table
    :param write_capacity_units: WCU configuration when creating the table
    :param read_capacity_units: RCU configuration when creating the table
    :param create: if True, create the table when initializing the backend,
        if table already exists, then do nothing. if False, you should create
        the table manually before using the backend.
    """

    def __init__(
        self,
        table_name: str,
        region: str,
        billing_mode: T.Optional[str] = PAY_PER_REQUEST_BILLING_MODE,
        write_capacity_units: T.Optional[int] = None,
        read_capacity_units: T.Optional[int] = None,
        create: bool = True,
    ):
        meta_kwargs = dict(
            table_name=table_name,
            region=region,
        )
        if billing_mode:
            meta_kwargs["billing_mode"] = billing_mode
        if write_capacity_units:  # pragma: no cover
            meta_kwargs["write_capacity_units"] = write_capacity_units
        if read_capacity_units:  # pragma: no cover
            meta_kwargs["read_capacity_units"] = read_capacity_units

        Meta_ = type("Meta", tuple(), meta_kwargs)

        class DynamoDBTable(Model):
            """
            The Dynamodb table backend for :class:`DynamodbCache`.

            Base Dynamodb cache backend. You can customize the behavior by adding
            custom serializer / deserializer.
            """

            Meta = Meta_

            key: str = UnicodeAttribute(hash_key=True)
            value: bytes = BinaryAttribute(legacy_encoding=False)
            expire: int = NumberAttribute()
            update_ts: int = NumberAttribute()

        self.Table: DynamoDBTable = DynamoDBTable

        if create:
            self.create_table()

    def create_table(self):
        self.Table.create_table(wait=True)

    def _set_record_to_backend(self, key: str, record: CacheRecord):
        self.Table(
            key=key,
            value=record.value,
            expire=record.expire,
            update_ts=record.update_ts,
        ).save()

    def _get_record_from_backend(self, key: str) -> T.Optional[CacheRecord]:
        item = self.Table.get_one_or_none(key)
        if item is None:
            return item
        else:
            return CacheRecord(
                value=item.value,
                expire=item.expire,
                update_ts=item.update_ts,
            )

    def clear_all(self):  # pragma: no cover
        self.Table.delete_all()

    def clear_expired(self):  # pragma: no cover
        raise NotImplementedError


class JsonDictDynamodbCache(
    DynamoDBBackend[dict],
):
    """
    A built-in Dynamodb cache designed to store JSON serializable dict.
    """

    def serialize(self, value: dict) -> bytes:
        return json.dumps(value).encode("utf-8")

    def deserialize(self, value: bytes) -> dict:
        return json.loads(value.decode("utf-8"))


class JsonListDynamodbCache(
    DynamoDBBackend[list],
):
    """
    A built-in Dynamodb cache designed to store JSON serializable list.
    """

    def serialize(self, value: list) -> bytes:
        return json.dumps(value).encode("utf-8")

    def deserialize(self, value: bytes) -> list:
        return json.loads(value.decode("utf-8"))
