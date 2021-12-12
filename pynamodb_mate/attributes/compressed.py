# -*- coding: utf-8 -*-

import gzip
import json
from typing import Optional
from pynamodb.attributes import BinaryAttribute


class CompressedJSONAttribute(BinaryAttribute):
    """
    A compressed unicode Attribute.

    Dump to unicode json string, encode to unicode bytes string
    and compress it internally.
    """

    def serialize(self, value) -> Optional[bytes]:
        return gzip.compress(
            json.dumps(value, ensure_ascii=False).encode("utf-8")
        )

    def deserialize(self, value):
        return json.loads(gzip.decompress(value).decode("utf-8"), strict=False)


class CompressedUnicodeAttribute(BinaryAttribute):
    """
    A compressed unicode Attribute.

    Encode to unicode bytes string and compress it internally.
    """

    def serialize(self, value: str) -> Optional[bytes]:
        return gzip.compress(value.encode("utf-8"))

    def deserialize(self, value: bytes) -> Optional[str]:
        return gzip.decompress(value).decode("utf-8")


class CompressedBinaryAttribute(BinaryAttribute):
    """
    A compressed binary Attribute.

    Compress it internally.
    """
    def serialize(self, value: bytes) -> Optional[bytes]:
        return gzip.compress(value)

    def deserialize(self, value):
        return gzip.decompress(value)
