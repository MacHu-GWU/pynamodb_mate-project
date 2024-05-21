# -*- coding: utf-8 -*-

"""
Store big binary or text in S3 and store the s3 object path in DynamoDB.
"""

import typing as T
import gzip
import json
import warnings

import boto3
from pynamodb.attributes import (
    UnicodeAttribute,
)
from ..helpers import sha256, join_s3_uri, split_s3_uri, is_s3_object_exists

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client


class S3BackedAttribute(UnicodeAttribute):
    """
    S3BackedAttribute will store the original data on S3 and store the S3 uri
    in DynamoDB.

    TODO: add automatically rollback if one of the DynamoDB write or S3 write failed.

    TODO: add an option to delete the S3 object as well when the DynamoDB item is deleted.

    :param bucket_name:
    :param key_template: the template of the S3 key. It must contain "{fingerprint}",
        and the {fingerprint} is the sha256 of the data
    :param compressed: whether to compress the data before storing it on S3.
    :param s3_client: the boto3 s3 client to read/write data to S3, it is useful
        if you want to use multiple s3 bucket that with different AWS credential.

    Other parameters are the same as ``pynamodb.attributes.UnicodeAttribute``.

    .. deprecated:: 5.5.1.1
    """

    def __init__(
        self,
        bucket_name: str,
        key_template: str = "pynamodb-mate/s3backed/{fingerprint}",
        compressed: bool = True,
        s3_client: T.Optional["S3Client"] = None,
        hash_key: bool = False,
        range_key: bool = False,
        null: T.Optional[bool] = None,
        default: T.Optional[T.Callable] = None,
        default_for_new: T.Optional[T.Callable] = None,
        attr_name: T.Optional[str] = None,
    ):
        warnings.warn(
            (
                "pynamodb_mate.attributes.s3backed.S3BackedAttribute, "
                "pynamodb_mate.attributes.s3backed.S3BackedBigBinaryAttribute, "
                "pynamodb_mate.attributes.s3backed.S3BackedBigTextAttribute, "
                "pynamodb_mate.attributes.s3backed.S3BackedJsonDictAttribute "
                "are deprecated, they will be removed in 6.X. You should use "
                "pynamodb_mate.patterns.large_attribute.api instead."
            ),
            DeprecationWarning,
        )
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            null=null,
            default=default,
            default_for_new=default_for_new,
            attr_name=attr_name,
        )
        if "{fingerprint}" not in key_template:
            raise ValueError(
                "key_template must contain '{fingerprint}'! "
                "it is the sha256 of the data."
            )
        self.bucket_name = bucket_name
        self.key_template = key_template
        self.compressed = compressed
        self.s3_client = s3_client or boto3.client("s3")

    def _get_s3_key_from_data(self, value: bytes) -> T.Tuple[str, str]:
        """
        Calculate the S3 uri to store the binary data.
        """
        fingerprint = sha256(value)
        s3_key = self.key_template.format(fingerprint=fingerprint)
        s3_uri = join_s3_uri(self.bucket_name, s3_key)
        return s3_key, s3_uri

    def _get_data_from_s3(self, value: str) -> bytes:
        """
        Given the S3 uri, get the original binary data from S3.
        """
        s3_bucket, s3_key = split_s3_uri(value)
        res = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        if self.compressed:
            return gzip.decompress(res["Body"].read())
        else:
            return res["Body"].read()

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

    def serialize(self, value: T.Any) -> str:
        """
        Take the original value, store it on S3 and return the S3 uri.
        """
        binary_view = self.user_serializer(value)
        s3_key, s3_uri = self._get_s3_key_from_data(binary_view)
        if not is_s3_object_exists(self.s3_client, self.bucket_name, s3_key):
            kwargs = dict(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            if self.compressed:
                kwargs["Body"] = gzip.compress(binary_view)
            else:
                kwargs["Body"] = binary_view
            self.s3_client.put_object(**kwargs)
        return s3_uri

    def deserialize(self, value: str) -> T.Any:
        """
        Take the S3 uri, get the original value from S3.
        """
        s3_uri = value
        binary_view = self._get_data_from_s3(s3_uri)
        return self.user_deserializer(binary_view)


class S3BackedBigBinaryAttribute(S3BackedAttribute):
    """
    An attribute that store big binary dict in S3 and store the S3 uri in DynamoDB.
    """

    def user_serializer(self, value: bytes) -> bytes:
        return value

    def user_deserializer(self, value: bytes) -> bytes:
        return value


class S3BackedBigTextAttribute(S3BackedAttribute):
    """
    An attribute that store big text dict in S3 and store the S3 uri in DynamoDB.
    """

    def user_serializer(self, value: str) -> bytes:
        return value.encode("utf-8")

    def user_deserializer(self, value: bytes) -> str:
        return value.decode("utf-8")


class S3BackedJsonDictAttribute(S3BackedAttribute):
    """
    An attribute that store big json dict in S3 and store the S3 uri in DynamoDB.
    """

    def user_serializer(self, value: dict) -> bytes:
        return json.dumps(value).encode("utf-8")

    def user_deserializer(self, value: bytes) -> dict:
        return json.loads(value.decode("utf-8"))
