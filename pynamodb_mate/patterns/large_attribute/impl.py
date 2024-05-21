# -*- coding: utf-8 -*-

"""
**Developer note [CN]**

这个模块的目的是提供了一些方便的函数用与帮你保证 DynamoDB 和 S3 双写一致性问题.
根据我在 https://learn-aws.readthedocs.io/search.html?q=Storage+Large+Item+in+DynamoDB&check_keywords=yes&area=default#
博文中的详细探讨, Create / Update 时应该先写 S3, 再写 DynamoDB, Delete 时先删 DynamoDB 再删 S3.

这个模块并没有将 S3 和 DynamoDB 的操作封装到一个函数中, 而是有意将两个操作分别用一个函数实现,
然后让用户来决定如何将其组合起来. 这是因为 DynamoDB 中的 update 操作不止需要更新 Large Attribute,
还可能需要更新其他 attribute, 这些操作我们无法预知, 应该交给用户来决定.

这个模块还解决了一个问题对于 DynamoDB 而言, 更新多个 attributes 是一个 update 原子操作,
但是对于 S3 而言, 每个 put_object 是一个独立操作. 如何保证原子性就是一个挑战. 并且当
Large Attribute value 没有变化时, put_object 到 S3 是非必要的, 所以我们需要
一个 PutS3Response 对象来追踪在这个 update 操作中, 哪些 attribute 所对应的
S3 object 修改了, 然后在 DynamoDB 操作失败时, 进行一些 clean up 工作.
"""

import typing as T
import hashlib
import dataclasses
from datetime import datetime

from pynamodb.constants import STRING

from ...helpers import join_s3_uri, is_s3_object_exists

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client
    from ...models import Model


def get_md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def get_s3_key(
    pk: T.Union[str, int],
    sk: T.Optional[T.Union[str, int]],
    attr: str,
    value: bytes,
    prefix: str,
) -> str:
    parts = list()
    if prefix:  # pragma: no cover
        if prefix.startswith("/"):
            prefix = prefix[1:]
        elif prefix.endswith("/"):
            prefix = prefix[:-1]
        parts.append(prefix)
    parts.append(f"pk={pk}")
    if sk is not None:  # pragma: no cover
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
    """ """

    attr: str
    s3_uri: str
    put_executed: bool


@dataclasses.dataclass
class PutS3Response:
    """
    The returned object for :meth:`LargeAttributeMixin.put_s3` method.

    It tells you the list of attributes got updated and their s3 location, and
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
        s3_client: "S3Client",
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
        s3_client: "S3Client",
        old_model: T.Union["Model", "LargeAttributeMixin"],
    ):
        """
        Call this method to clean up when the ``pynamodb_mate.Model(...).update(...)``
        operation succeeded. Because when you changed the value of the large attribute,
        you actually created a new S3 object. This method can help you clean up the
        old S3 object.

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
        s3_client: "S3Client",
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
        s3_client: T.Union["S3Client", T.Dict[str, "S3Client"]],
        pk: T.Union[str, int],
        sk: T.Optional[T.Union[str, int]],
        kvs: T.Dict[str, bytes],
        bucket: str,
        prefix: str,
        update_at: datetime,
    ) -> PutS3Response:
        """
        Put large attribute data to S3.

        :param s3_client: single ``boto3.client("s3")`` object if all large attributes are
            in the same AWS Account. If you have multiple large attributes in
            different AWS Account, then you should pass a dict of s3 client.
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
        s3_client_is_dict = isinstance(s3_client, dict)
        if s3_client_is_dict is False:
            s3_client_mapper = dict()
        else:
            s3_client_mapper = s3_client
        for k in kvs:
            if k not in attrs:
                raise AttributeError(f"Key {k} not found in attributes")
            if attrs[k].attr_type != STRING:
                raise TypeError(
                    f"The large attribute type has to be UnicodeAttribute, "
                    f"but yours: {k}: {attrs[k].attr_type}!"
                )
            if s3_client_is_dict is False:
                s3_client_mapper[k] = s3_client
        put_s3_response = PutS3Response(actions=[])
        for attr, value in kvs.items():
            metadata = {"pk": pk}
            if sk is not None:
                metadata["sk"] = sk
            metadata["attr"] = attr
            metadata["update_at"] = update_at.isoformat()
            s3_key = get_s3_key(pk=pk, sk=sk, attr=attr, value=value, prefix=prefix)
            s3_uri = join_s3_uri(bucket, s3_key)
            _s3_client = s3_client_mapper[attr]
            if is_s3_object_exists(_s3_client, bucket=bucket, key=s3_key):
                put_s3_response.actions.append(
                    Action(attr=attr, s3_uri=s3_uri, put_executed=False)
                )
            else:
                _s3_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=value,
                    Metadata=metadata,
                )
                put_s3_response.actions.append(
                    Action(attr=attr, s3_uri=s3_uri, put_executed=True)
                )
        return put_s3_response
