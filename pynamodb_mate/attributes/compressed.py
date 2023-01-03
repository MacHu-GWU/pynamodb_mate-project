# -*- coding: utf-8 -*-

"""
Auto-compress and decompress data in DynamoDB.
"""

import typing as T
import gzip
import json

from pynamodb.attributes import BinaryAttribute


class CompressedAttribute(BinaryAttribute):
    """
    CompressedAttribute will serialize the original data to binary format,
    and compress it before sending to DynamoDB.
    """

    def user_serializer(self, value: T.Any) -> bytes:  # pragma: no cover
        """
        Implement this method to define how you want to convert your data to binary.
        """
        raise NotImplementedError

    def user_deserializer(self, value: bytes) -> T.Any:  # pragma: no cover
        """
        Implement this method to define how you want to recover your data from binary.
        """
        raise NotImplementedError

    def serialize(self, value: T.Any) -> bytes:
        return gzip.compress(self.user_serializer(value))

    def deserialize(self, value: bytes) -> T.Any:
        return self.user_deserializer(gzip.decompress(value))


class CompressedBinaryAttribute(CompressedAttribute):
    """
    A compressed binary Attribute.
    """

    def user_serializer(self, value: T.Any) -> bytes:
        return value

    def user_deserializer(self, value: bytes) -> T.Any:
        return value


class CompressedUnicodeAttribute(CompressedAttribute):
    """
    A compressed unicode Attribute.
    """

    def user_serializer(self, value: T.Any) -> bytes:
        return value.encode("utf-8")

    def user_deserializer(self, value: bytes) -> T.Any:
        return value.decode("utf-8")


class CompressedJSONDictAttribute(CompressedAttribute):
    """
    A compressed JSON dict Attribute.
    """

    def user_serializer(self, value: dict) -> bytes:
        return json.dumps(value).encode("utf-8")

    def user_deserializer(self, value: bytes) -> dict:
        return json.loads(value.decode("utf-8"))
