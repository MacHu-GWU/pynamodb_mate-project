# -*- coding: utf-8 -*-

import typing as T
import hashlib
import dataclasses
from datetime import datetime, timezone

from pynamodb.constants import STRING

from ...helpers import join_s3_uri, is_s3_object_exists

if T.TYPE_CHECKING:
    from ...models import Model


def get_md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def get_utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def get_s3_key(
    pk: T.Union[str, int],
    sk: T.Optional[T.Union[str, int]],
    attr: str,
    value: bytes,
    prefix: str,
) -> str:
    parts = list()
    if prefix:
        if prefix.startswith("/"):
            prefix = prefix[1:]
        elif prefix.endswith("/"):
            prefix = prefix[:-1]
        parts.append(prefix)
    parts.append(f"pk={pk}")
    if sk is not None:
        parts.append(f"sk={sk}")
    parts.append(f"attr={attr}")
    md5 = get_md5(value)
    parts.append(f"md5={md5}")
    return "/".join(parts)


def split_s3_uri(s3_uri: str) -> T.Tuple[str, str]:
    parts = s3_uri.split("/", 3)
    return parts[2], parts[3]


@dataclasses.dataclass
class Action:
    attr: str
    s3_uri: str
    put_executed: bool


@dataclasses.dataclass
class PutS3Response:
    """
    The returned object for :meth:`LargeAttributeMixin.put_s3` method.

    It tell you the list of attributes got updated and their s3 location, and
    whether the s3 put object API call happened. This is very helpful when the
    subsequent DynamoDB operation failed.
    """

    actions: T.List[Action]

    def to_attributes(self) -> T.Dict[str, str]:
        """
        Convert this object to the params for ``pynamodb_model.Model`` constructor.
        """
        return {action.attr: action.s3_uri for action in self.actions}

    def batch_delete(
        self,
        s3_client,
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
        for s3_uri in s3_uri_list:
            bucket, key = split_s3_uri(s3_uri)
            buckets.append(bucket)
            keys.append(key)

        n_unique_bucket = len(set(buckets))
        if n_unique_bucket == 0:
            pass
        elif n_unique_bucket == 1:
            s3_client.delete_objects(
                Bucket=buckets[0],
                Delete=dict(Objects=[dict(Key=key) for key in keys]),
            )
        else:
            for bucket, key in zip(buckets, keys):
                s3_client.delete_object(Bucket=bucket, Key=key)

    def clean_up_when_create_dynamodb_item_failed(
        self,
        s3_client,
    ):
        """
        Call this method to clean up when the ``pynamodb_mate.Model(...).save()``
        operation failed.

        :param s3_client: ``boto3.client("s3")`` object.
        """
        s3_uri_list = list()
        for action in self.actions:
            if action.put_executed:
                s3_uri_list.append(action.s3_uri)
        self.batch_delete(s3_client, s3_uri_list)

    def clean_up_when_update_dynamodb_item_succeeded(
        self,
        s3_client,
        old_model: T.Union["Model", "LargeAttributeMixin"],
    ):
        """
        Call this method to clean up when the ``pynamodb_mate.Model(...).update(...)``
        operation failed.

        :param s3_client: ``boto3.client("s3")`` object.
        :param old_model: the old model object before updating it, we need this
            to figure out where to delete old S3 object.
        """
        s3_uri_list = list()
        for action in self.actions:
            # 如果新创建了一个 object, 并且这个 object 跟之前的版本不一样,
            # 那么可以安全删掉旧的 object
            if action.put_executed and (
                action.s3_uri != getattr(old_model, action.attr)
            ):
                s3_uri_list.append(getattr(old_model, action.attr))
        self.batch_delete(s3_client, s3_uri_list)

    def clean_up_when_update_dynamodb_item_failed(
        self,
        s3_client,
        old_model: T.Union["Model", "LargeAttributeMixin"],
    ):
        """
        Call this method to clean up when the ``pynamodb_mate.Model(...).update(...)``
        operation failed.

        :param s3_client: ``boto3.client("s3")`` object.
        :param old_model: the old model object before updating it, we need this
            to figure out whether the old S3 object got changed.
        """
        s3_uri_list = list()
        for action in self.actions:
            # 如果新创建了一个 object, 并且这个 object 跟之前的版本不一样,
            # 那么可以安全删掉新的 object
            if action.put_executed and (
                action.s3_uri == getattr(old_model, action.attr)
            ):
                s3_uri_list.append(action.s3_uri)
        self.batch_delete(s3_client, s3_uri_list)


class LargeAttributeMixin:
    """
    A mixin class that should inject along with ``pynamodb_mate.Model``.
    """

    @classmethod
    def put_s3(
        cls: T.Type["Model"],
        s3_client,
        pk: T.Union[str, int],
        sk: T.Optional[T.Union[str, int]],
        kvs: T.Dict[str, bytes],
        bucket: str,
        prefix: str,
        update_at: datetime,
    ) -> PutS3Response:
        """
        Put large attribute data to S3.

        :param s3_client:
        :param pk: partition key.
        :param sk: sort key, use None if no sort key.
        :param kvs: key value pairs of the large attribute data. The key is the
            attribute name, the value is the data in binary format. For example,
            you have two large attributes in your data model, "html" and "image".
            Then the ``kvs`` should be
            ``{"html": "html text".encode("utf-8"), "image": b"image content"}``
        :param bucket: S3 bucket name.
        :param prefix: common prefix.
        :param update_at: this update_at will be used in S3 metadata so that
            you can identify unused S3 objects in clean-up operation. You should
            also use this value in your data model if you have an attribute
            to show the DynamoDB item update time.

        :rtype: :class:`PutS3Response`.
        """
        attrs = cls.get_attributes()
        for k in kvs:
            if k not in attrs:
                raise AttributeError(f"Key {k} not found in attributes")
            if attrs[k].attr_type != STRING:
                raise TypeError(
                    f"The large attribute type has to be UnicodeAttribute, "
                    f"but yours: {k}: {attrs[k].attr_type}!"
                )
        put_s3_response = PutS3Response(actions=[])
        for attr, value in kvs.items():
            metadata = {"pk": pk}
            if sk is not None:
                metadata["sk"] = sk
            metadata["attr"] = attr
            metadata["update_at"] = update_at.isoformat()
            s3_key = get_s3_key(pk=pk, sk=sk, attr=attr, value=value, prefix=prefix)
            s3_uri = join_s3_uri(bucket, s3_key)
            if is_s3_object_exists(s3_client, bucket=bucket, key=s3_key):
                put_s3_response.actions.append(
                    Action(attr=attr, s3_uri=s3_uri, put_executed=False)
                )
            else:
                s3_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=value,
                    Metadata=metadata,
                )
                put_s3_response.actions.append(
                    Action(attr=attr, s3_uri=s3_uri, put_executed=True)
                )
        return put_s3_response