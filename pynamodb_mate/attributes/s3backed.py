# -*- coding: utf-8 -*-

import gzip
import typing

from pynamodb.attributes import (
    UnicodeAttribute,
)
from ..helpers import (
    sha256, join_s3_uri, split_s3_uri, is_s3_object_exists
)



class S3BackedAttribute(UnicodeAttribute):
    """
    **中文文档**

    没有办法从 Attribute 对象中访问到上级的 Model 对象.
    """
    bucket_name = None
    s3_client = None

    _is_s3_backed = True

    def get_s3_key(self, fingerprint: str) -> str:
        raise NotImplementedError

    def get_fingerprint(self, value: typing.Union[str, bytes]) -> str:
        raise NotImplementedError


S3KEY_BIGBINARY = "pynamodb-mate/bigbinary/{}.dat"
S3KEY_BIGTEXT = "pynamodb-mate/bigtext/{}.txt"

class S3BackedBigBinaryAttribute(S3BackedAttribute):
    def get_s3_key(self, fingerprint: str) -> str:
        return S3KEY_BIGBINARY.format(fingerprint)

    def serialize(self, value: bytes) -> str:
        fingerprint = sha256(value)
        s3_bucket = self.bucket_name
        s3_key = self.get_s3_key(fingerprint)
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
        res = self.s3_client.get_object(
            Bucket=s3_bucket,
            Key=s3_key
        )
        return gzip.decompress(res["Body"].read())


class S3BackedBigTextAttribute(S3BackedAttribute):
    def get_s3_key(self, fingerprint: str) -> str:
        return S3KEY_BIGTEXT.format(fingerprint)

    def serialize(self, value: str) -> str:
        b_value = value.encode("utf-8")
        fingerprint = sha256(b_value)
        s3_bucket = self.bucket_name
        s3_key = self.get_s3_key(fingerprint)
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
        res = self.s3_client.get_object(
            Bucket=s3_bucket,
            Key=s3_key
        )
        return gzip.decompress(res["Body"].read()).decode("utf-8")
