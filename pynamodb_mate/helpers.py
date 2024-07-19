# -*- coding: utf-8 -*-

import typing as T
import base64
import hashlib

from botocore.exceptions import ClientError
from .vendor.iterable import group_by

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client


def bytes_to_base85str(b: bytes) -> str:
    """ """
    return base64.b85encode(b).decode("utf-8")


def base85str_to_bytes(s: str) -> bytes:
    """ """
    return base64.b85decode(s.encode("utf-8"))


def sha256(b: bytes) -> str:
    """ """
    m = hashlib.sha256()
    m.update(b)
    return m.hexdigest()


def split_s3_uri(s3_uri: str) -> T.Tuple[str, str]:
    """
    Split AWS S3 URI, returns bucket and key.
    """
    parts = s3_uri.split("/")
    bucket = parts[2]
    key = "/".join(parts[3:])
    return bucket, key


def join_s3_uri(bucket: str, key: str) -> str:
    """
    Join AWS S3 URI from bucket and key.
    """
    return "s3://{}/{}".format(bucket, key)


def is_s3_object_exists(
    s3_client: "S3Client", bucket: str, key: str
) -> bool:  # pragma: no cover
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        return False
    except:
        raise


def remove_s3_prefix(s3_client: "S3Client", bucket: str, prefix: str):
    """
    Remove all objects with the same prefix in the bucket.
    """
    res = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
    for content in res.get("Contents", []):
        key = content["Key"]
        s3_client.delete_object(Bucket=bucket, Key=key)


def batch_delete_s3_objects(
    s3_client: "S3Client",
    s3_uri_list: T.List[str],
):
    """
    Batch delete many S3 objects. If they share the same bucket, then use
    the ``s3_client.delete_objects`` method. If they do not share the same bucket,
    then use ``s3_client.delete_object`` method.

    :param s3_client: ``boto3.client("s3")`` object.
    :param s3_uri_list: example: ["s3://bucket/key1", "s3://bucket/key2"].
    """
    buckets = list()
    keys = list()
    pairs = list()
    for s3_uri in s3_uri_list:
        bucket, key = split_s3_uri(s3_uri)
        pairs.append((bucket, key))

        buckets.append(bucket)
        keys.append(key)

    groups = group_by(pairs, get_key=lambda x: x[0])
    for bucket, bucket_key_pairs in groups.items():
        if len(bucket_key_pairs):
            s3_client.delete_objects(
                Bucket=bucket,
                Delete=dict(Objects=[dict(Key=key) for _, key in bucket_key_pairs]),
            )
