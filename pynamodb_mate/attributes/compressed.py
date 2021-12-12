# -*- coding: utf-8 -*-

import gzip
import json
from typing import Optional
from pynamodb.attributes import BinaryAttribute


class CompressedJSONAttribute(BinaryAttribute):
    """
    A JSON Attribute

    Encodes JSON to unicode internally
    """

    def serialize(self, value) -> Optional[bytes]:
        if value is None: # pragma: no cover
            return None
        return gzip.compress(json.dumps(value).encode("utf-8"))

    def deserialize(self, value):
        return json.loads(gzip.decompress(value).decode("utf-8"), strict=False)
