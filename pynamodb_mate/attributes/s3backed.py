# -*- coding: utf-8 -*-
import typing

from pynamodb.attributes import (
    UnicodeAttribute,
    Optional, Union, _T, Callable, Any
)
from ..helpers import (
    sha256, join_s3_uri, split_s3_uri
)


class S3BackedAttribute(UnicodeAttribute):
    def __init__(
        self,
        hash_key: bool = False,
        range_key: bool = False,
        null: Optional[bool] = None,
        default: Optional[Union[_T, Callable[..., _T]]] = None,
        default_for_new: Optional[Union[Any, Callable[..., _T]]] = None,
        attr_name: Optional[str] = None,
        bucket_name: str = None,
        s3_client=None,
    ):
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            null=null,
            default=default,
            default_for_new=default_for_new,
            attr_name=attr_name,
        )
        if bucket_name is None:
            raise ValueError
        self.bucket_name = bucket_name
        self.s3_client = s3_client

    def get_s3_key(self, fingerprint):
        return "pynamodb-mate/bigbinary/{}.dat".format(fingerprint)


class S3BackedBigBinaryAttribute(S3BackedAttribute):
    def serialize(self, value: bytes) -> str:
        print(self.__class__)
        fingerprint = sha256(value)
        s3_bucket = self.bucket_name
        s3_key = self.get_s3_key(fingerprint)
        s3_uri = join_s3_uri(s3_bucket, s3_key)
        self.s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=value,
        )
        return s3_uri

    def deserialize(self, value: str) -> bytes:
        s3_bucket, s3_key = split_s3_uri(value)
        res = self.s3_client.get_object(
            Bucket=s3_bucket,
            Key=s3_key
        )
        binary_data = res["Body"].read()
        return binary_data


class S3BackedBigTextAttribute(S3BackedAttribute):
    def serialize(self, value: str) -> str:
        fingerprint = sha256(value.encode("utf-8"))
        s3_bucket = self.bucket_name
        s3_key = self.get_s3_key(fingerprint)
        s3_uri = join_s3_uri(s3_bucket, s3_key)
        self.s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=value,
        )
        return s3_uri

    def deserialize(self, value: str) -> str:
        s3_bucket, s3_key = split_s3_uri(value)
        res = self.s3_client.get_object(
            Bucket=s3_bucket,
            Key=s3_key
        )
        text_data = res["Body"].read().decode("utf-8")
        return text_data
