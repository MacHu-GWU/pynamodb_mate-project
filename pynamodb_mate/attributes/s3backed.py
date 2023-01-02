# -*- coding: utf-8 -*-

"""
Store big binary or text in S3 and store the s3 object path in DynamoDB.
"""

import gzip

from pynamodb.attributes import (
    UnicodeAttribute,
)
from ..helpers import sha256, join_s3_uri, split_s3_uri, is_s3_object_exists


class S3BackedAttribute(UnicodeAttribute):
    """
    **中文文档**

    没有办法从 Attribute 对象中访问到上级的 Model 对象, 所以只能自己传入每个 attribute
    的参数.
    """

    bucket_name = None
    key_template = None
    s3_client = None

    _is_s3_backed = True

    def _get_s3_key(self, fingerprint: str) -> str:
        return self.key_template.format(fingerprint=fingerprint)


class S3BackedBigBinaryAttribute(S3BackedAttribute):
    """
    Representation of a binary attribute.
    """
    key_template = "pynamodb-mate/bigbinary/{fingerprint}.dat"

    def serialize(self, value: bytes) -> str:
        fingerprint = sha256(value)
        s3_bucket = self.bucket_name
        s3_key = self._get_s3_key(fingerprint)
        s3_uri = join_s3_uri(s3_bucket, s3_key)
        if not is_s3_object_exists(self.s3_client, s3_bucket, s3_key):
            self.s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=gzip.compress(value),
            )
        return s3_uri

    def deserialize(self, value: str) -> bytes:
        s3_bucket, s3_key = split_s3_uri(value)
        res = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        return gzip.decompress(res["Body"].read())


class S3BackedBigTextAttribute(S3BackedAttribute):
    """
    Representation of a text attribute.
    """
    key_template = "pynamodb-mate/bigtext/{fingerprint}.txt"

    def serialize(self, value: str) -> str:
        b_value = value.encode("utf-8")
        fingerprint = sha256(b_value)
        s3_bucket = self.bucket_name
        s3_key = self._get_s3_key(fingerprint)
        s3_uri = join_s3_uri(s3_bucket, s3_key)
        if not is_s3_object_exists(self.s3_client, s3_bucket, s3_key):
            self.s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=gzip.compress(b_value),
            )
        return s3_uri

    def deserialize(self, value: str) -> str:
        s3_bucket, s3_key = split_s3_uri(value)
        res = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        return gzip.decompress(res["Body"].read()).decode("utf-8")
