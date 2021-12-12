# -*- coding: utf-8 -*-

import typing
import base64
import hashlib
from botocore.exceptions import ClientError


def bytes_to_base85str(b: bytes) -> str:
    """
    """
    return base64.b85encode(b).decode("utf-8")


def base85str_to_bytes(s: str) -> bytes:
    """
    """
    return base64.b85decode(s.encode("utf-8"))


def sha256(b: bytes) -> str:
    """
    """
    m = hashlib.sha256()
    m.update(b)
    return m.hexdigest()


def split_s3_uri(s3_uri: str) -> typing.Tuple[str, str]:
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


def is_s3_object_exists(s3_client, bucket: str, key: str) -> bool:  # pragma: no cover
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        return False
    except:
        raise


def remove_s3_prefix(s3_client, bucket, prefix):
    res = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
    for content in res.get("Contents", []):
        key = content["Key"]
        s3_client.delete_object(Bucket=bucket, Key=key)
