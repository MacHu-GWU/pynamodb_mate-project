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
import copy
import hashlib
import dataclasses
from datetime import datetime, timedelta

from pynamodb.constants import STRING
from pynamodb.expressions.update import Action

from ...helpers import join_s3_uri, is_s3_object_exists, batch_delete_s3_objects

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
    """
    Figure out the S3 key location for the large attribute based on the DynamoDB
    item's partition key, sort key, attribute name, and the value of the attribute.

    :param pk: partition key.
    :param sk: sort key, use None if no sort key.
    :param attr: large attribute name.
    :param value: large attribute value in binary format.
    :param prefix: common S3 prefix.

    :return: example "${prefix}/pk={pk}/sk={sk}/attr={attr}/md5={md5}"
    """
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


T_S3_KEY_GETTER = T.Callable[
    [
        T.Union[str, int],
        T.Optional[T.Union[str, int]],
        str,
        bytes,
        str,
    ],
    str,
]


def split_s3_uri(s3_uri: str) -> T.Tuple[str, str]:
    parts = s3_uri.split("/", 3)
    return parts[2], parts[3]


@dataclasses.dataclass
class Action:
    """
    表示一个 put_object 操作是否执行了, 以及执行的结果. 由于我们使用 content based hash
    作为 S3 URI 的一部分, 一旦 S3 object 已经存在, 我们是不会执行 s3_client.put_object 操作的.
    换言之, 一旦我们执行了, 那么这个 DynamoDB attribute 的值肯定改变了 (换了一个 S3 URI).

    :param attr: DynamoDB attribute name.
    :param s3_uri: S3 object URI.
    :param put_executed: Whether the s3_client.put_object API call happened.
    """

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
        When you want to create a new DynamoDB item after you put the large attribute
        S3 object, you can use this method to get the params for
        ``pynamodb_model.api.Model(**attributes)`` constructor.
        Note that if an action.put_executed is False, then it means that the
        S3 object already exists, so we still consider the "set large attribute"
        operation is succeeded.
        """
        dct = dict()
        for action in self.actions:
            dct[action.attr] = action.s3_uri
        return dct

    def to_update_actions(self, model_klass) -> T.List[Action]:
        """
        When you want to update an existing DynamoDB item after you put the large attribute
        S3 object, you can use this method to get large attributes related update actions
        for the ``pynamodb_model.api.Model(...).update(actions=update_actions)`` method.
        """
        return [
            getattr(model_klass, action.attr).set(action.s3_uri)
            for action in self.actions
        ]

    def clean_up_created_s3_object_when_create_dynamodb_item_failed(
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
        batch_delete_s3_objects(s3_client, s3_uri_list)

    def clean_up_old_s3_object_when_update_dynamodb_item_succeeded(
        self,
        s3_client: "S3Client",
        old_model: T.Union["Model", "LargeAttributeMixin"],
    ):
        """
        Call this method to clean up when the ``pynamodb_mate.Model(...).update(...)``
        operation succeeded. Because when you changed the value of the large attribute,
        you actually created a new S3 object. This method can clean up the old S3 object.

        :param s3_client: ``boto3.client("s3")`` object.
        :param old_model: the old model object before updating it, we need this
            to figure out where to delete old S3 object.
        """
        s3_uri_list = list()
        for action in self.actions:
            # 当 put_executed 为 False 时, 说明, 我们并没有创建新的 object, 换言之旧的
            # object 依然有效, 所以我们不需要再 DynamoDB update 成功时 clean up 旧的 object
            #
            # 而 put_executed 为 True 时, 所以我们一定是创建了新的 object 了, 那么
            # 有没有可能新的 uri 和 旧的 uri 相同呢? 这种情况下我们如果 clean up 旧的 object
            # 但实际上把新的 object 也删掉了, 这是不对的. 但是我认为这种事情不可能发生,
            # 因为如果新的 uri 和 旧的 uri 相同, 那么因为旧的 uri 存在则 S3 object 必然存在,
            # 这是由我们的一致性算法所保证的, 那么我们就不可能执行 put_object 操作. 所以我们没有
            # 必要检查新的 uri 和 旧的 uri 是否相同.
            if action.put_executed:
                # 删除旧的 S3 object
                s3_uri = getattr(old_model, action.attr)
                # 如果之前 attr 的值是 None, 那么我们就不需要删除 S3 object
                if s3_uri:
                    s3_uri_list.append(s3_uri)
        batch_delete_s3_objects(s3_client, s3_uri_list)

    def clean_up_created_s3_object_when_update_dynamodb_item_failed(
        self,
        s3_client: "S3Client",
    ):
        """
        Call this method to clean up when the ``pynamodb_mate.Model(...).update(...)``
        operation failed. Because you may have created a new S3 object, but since
        the DynamoDB update operation failed, you don't need the new S3 object.
        This method can clean up the new S3 object.

        :param s3_client: ``boto3.client("s3")`` object.
        """
        s3_uri_list = list()
        for action in self.actions:
            # 当 put_executed 为 False 时, 说明, 我们并没有创建新的 object, 换言之旧的
            # object 依然有效, 所以我们不需要再 DynamoDB update 失败时 clean up 新的 object
            #
            # 而 put_executed 为 True 时, 所以我们一定是创建了新的 object 了, 那么
            # 有没有可能新的 uri 和 旧的 uri 相同呢? 这种情况下我们如果 clean up 新的 object
            # 但实际上把旧的 object 也删掉了, 这是不对的. 但是我认为这种事情不可能发生,
            # 因为如果新的 uri 和 旧的 uri 相同, 那么因为旧的 uri 存在则 S3 object 必然存在,
            # 这是由我们的一致性算法所保证的, 那么我们就不可能执行 put_object 操作. 所以我们没有
            # 必要检查新的 uri 和 旧的 uri 是否相同.
            if action.put_executed:
                # 删除新的 S3 object
                s3_uri_list.append(action.s3_uri)
        batch_delete_s3_objects(s3_client, s3_uri_list)


class LargeAttributeMixin:
    """
    A mixin class that should inject along with ``pynamodb_mate.Model``.
    """

    @classmethod
    def put_s3(
        cls: T.Union[T.Type["Model"], T.Type["LargeAttributeMixin"]],
        s3_client: "S3Client",
        pk: T.Union[str, int],
        sk: T.Optional[T.Union[str, int]],
        kvs: T.Dict[str, bytes],
        bucket: str,
        prefix: str,
        update_at: datetime,
        s3_put_object_kwargs: T.Optional[T.Dict[str, T.Dict[str, T.Any]]] = None,
        s3_key_getter: T_S3_KEY_GETTER = get_s3_key,
    ) -> PutS3Response:
        """
        Put large attribute data to S3.

        :param s3_client: ``boto3.client("s3")`` object.
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
        :param s3_put_object_kwargs: additional arguments for ``s3_client.put_object``
            for each large attributes. for example ``{key: put_object_kwargs}``.
            The ``key`` is the large attribute name, the ``put_object_kwargs`` is
            a dictionary for ``s3_client.put_object`` method. For example, if you want
            to set metadata or ContentType for the S3 object, you can use this parameter.

        :rtype: :class:`PutS3Response`.
        """
        attrs = cls.get_attributes()
        for k in kvs:
            if k not in attrs:  # pragma: no cover
                raise AttributeError(f"Key {k} not found in attributes")
            if attrs[k].attr_type != STRING:  # pragma: no cover
                raise TypeError(
                    f"The large attribute type has to be UnicodeAttribute, "
                    f"but yours: {k}: {attrs[k].attr_type}!"
                )
        if s3_put_object_kwargs is None:
            s3_put_object_kwargs = dict()
        put_s3_response = PutS3Response(actions=[])
        for attr, value in kvs.items():
            s3_key = s3_key_getter(pk, sk, attr, value, prefix)
            s3_uri = join_s3_uri(bucket, s3_key)
            if is_s3_object_exists(s3_client, bucket=bucket, key=s3_key):
                put_executed = False
            else:
                put_object_kwargs = s3_put_object_kwargs.get(attr, {})
                additional_metadata = put_object_kwargs.get("Metadata", {})
                additional_metadata["pk"] = pk
                if sk is not None:  # pragma: no cover
                    additional_metadata["sk"] = sk
                additional_metadata["attr"] = attr
                additional_metadata["update_at"] = update_at.isoformat()
                s3_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=value,
                    Metadata=additional_metadata,
                    **put_object_kwargs,
                )
                put_executed = True
            put_s3_response.actions.append(
                Action(
                    attr=attr,
                    s3_uri=s3_uri,
                    put_executed=put_executed,
                )
            )
        return put_s3_response

    @classmethod
    def create_large_attribute_item(
        cls: T.Union[T.Type["Model"], T.Type["LargeAttributeMixin"]],
        s3_client: T.Union["S3Client", T.Dict[str, "S3Client"]],
        pk: T.Union[str, int],
        sk: T.Optional[T.Union[str, int]],
        kvs: T.Dict[str, bytes],
        bucket: str,
        prefix: str,
        update_at: datetime,
        s3_put_object_kwargs: T.Optional[T.Dict[str, T.Dict[str, T.Any]]] = None,
        s3_key_getter: T_S3_KEY_GETTER = get_s3_key,
        attributes: T.Optional[T.Dict[str, T.Any]] = None,
        clean_up_when_failed: bool = True,
        _error: T.Optional[Exception] = None,
    ):
        """
        Wrap the DynamoDB put_item and S3 put_object operation in a transaction.

        :param s3_client: ``boto3.client("s3")`` object.
        :param pk: hash key value of the DynamoDB item.
        :param sk: range key value if your DynamoDB table has range key, otherwise
            use None.
        :param kvs: key value mapper in Python dictionary for large attribute name
            and binary data. All data has to be encoded in binary format.
        :param bucket: S3 bucket to store the large attribute data.
        :param prefix: S3 prefix to store the large attribute data, the final S3 key
            would be ``s3://{bucket}/{prefix}/pk={pk}/sk={sk}/attr={attr}/md5={md5}``.
        :param update_at: the update time of the DynamoDB item, it will be stored
            in the S3 object metadata as well.
        :param s3_put_object_kwargs: additional arguments for ``s3_client.put_object``
            for each large attributes. for example ``{key: put_object_kwargs}``.
            The ``key`` is the large attribute name, the ``put_object_kwargs`` is
            a dictionary for ``s3_client.put_object`` method. For example, if you want
            to set metadata or ContentType for the S3 object, you can use this parameter.
        :param attributes: additional DynamoDB item attributes other than
            large attributes you want to set.
        :param clean_up_when_failed: if True, if S3 write succeeded
            and DynamoDB create item failed, the created S3 object will be deleted.
        """
        put_s3_res = cls.put_s3(
            s3_client=s3_client,
            pk=pk,
            sk=sk,
            kvs=kvs,
            bucket=bucket,
            prefix=prefix,
            update_at=update_at,
            s3_put_object_kwargs=s3_put_object_kwargs,
            s3_key_getter=s3_key_getter,
        )
        try:
            # this is for unit test purpose to simulate the DynamoDB operation failed
            if _error:
                raise _error
            kwargs = dict(**attributes, **put_s3_res.to_attributes())
            kwargs[cls._hash_keyname] = pk
            if cls._range_keyname:
                kwargs[cls._range_keyname] = sk
            model = cls(**kwargs)
            model.save()
            return model
        except Exception as e:
            if clean_up_when_failed:
                put_s3_res.clean_up_created_s3_object_when_create_dynamodb_item_failed(
                    s3_client
                )
            raise e

    @classmethod
    def update_large_attribute_item(
        cls: T.Union[T.Type["Model"], T.Type["LargeAttributeMixin"]],
        s3_client: T.Union["S3Client", T.Dict[str, "S3Client"]],
        pk: T.Union[str, int],
        sk: T.Optional[T.Union[str, int]],
        kvs: T.Dict[str, bytes],
        bucket: str,
        prefix: str,
        update_at: datetime,
        s3_put_object_kwargs: T.Optional[T.Dict[str, T.Dict[str, T.Any]]] = None,
        s3_key_getter: T_S3_KEY_GETTER = get_s3_key,
        update_actions: T.Optional[T.List[Action]] = None,
        consistent_read: bool = False,
        clean_up_when_succeeded: bool = True,
        clean_up_when_failed: bool = True,
        _error: T.Optional[Exception] = None,
    ):
        """
        Wrap the DynamoDB update_item and S3 put_object operation in a transaction.

        :param s3_client: ``boto3.client("s3")`` object.
        :param pk: hash key value of the DynamoDB item.
        :param sk: range key value if your DynamoDB table has range key, otherwise
            use None.
        :param kvs: key value mapper in Python dictionary for large attribute name
            and binary data. All data has to be encoded in binary format.
        :param bucket: S3 bucket to store the large attribute data.
        :param prefix: S3 prefix to store the large attribute data, the final S3 key
            would be ``s3://{bucket}/{prefix}/pk={pk}/sk={sk}/attr={attr}/md5={md5}``.
        :param update_at: the update time of the DynamoDB item, it will be stored
            in the S3 object metadata as well.
        :param s3_put_object_kwargs: additional arguments for ``s3_client.put_object``
            for each large attributes. for example ``{key: put_object_kwargs}``.
            The ``key`` is the large attribute name, the ``put_object_kwargs`` is
            a dictionary for ``s3_client.put_object`` method. For example, if you want
            to set metadata or ContentType for the S3 object, you can use this parameter.
        :param update_actions: additional DynamoDB item update expressions syntax
            other than large attributes you want to set. Please refer to
            https://pynamodb.readthedocs.io/en/latest/updates.html
        :param clean_up_when_succeeded: if True, if large attributes of old DynamoDB
            item got changed, the old S3 object will be deleted.
        :param clean_up_when_failed: if Ture, if S3 write succeeded
            and DynamoDB update item failed, the created S3 object will be deleted.
        """
        put_s3_res = cls.put_s3(
            s3_client=s3_client,
            pk=pk,
            sk=sk,
            kvs=kvs,
            bucket=bucket,
            prefix=prefix,
            update_at=update_at,
            s3_put_object_kwargs=s3_put_object_kwargs,
            s3_key_getter=s3_key_getter,
        )
        got_old_model = (
            False  # IDE show warning that this line is useless, but we do need it
        )
        try:
            # this is for unit test purpose to simulate the DynamoDB operation failed
            if _error:
                raise _error

            # get old model when we need to clean up
            if clean_up_when_succeeded:
                attributes_to_get = list(kvs)
                attributes_to_get.append(cls._hash_keyname)
                if cls._range_keyname:  # pragma: no cover
                    attributes_to_get.append(cls._range_keyname)
                old_model = cls.get(
                    hash_key=pk,
                    range_key=sk,
                    consistent_read=consistent_read,
                    attributes_to_get=attributes_to_get,
                )
            else:
                old_model = cls.make_one(hash_key=pk, range_key=sk)
            # old_model.update() API call will change the old_model object inplace,
            # so we need to keep a copy of the old_model object for clean up purpose.
            immutable_old_model = copy.copy(old_model)
            got_old_model = True

            # figure out the to-update actions
            actions = put_s3_res.to_update_actions(model_klass=cls)
            if update_actions:
                actions.extend(update_actions)
            res = old_model.update(actions=actions)
            new_model = cls.from_raw_data(res["Attributes"])

            if clean_up_when_succeeded:
                if got_old_model:
                    put_s3_res.clean_up_old_s3_object_when_update_dynamodb_item_succeeded(
                        s3_client=s3_client,
                        old_model=immutable_old_model,
                    )
            return new_model
        except Exception as e:
            if clean_up_when_failed:
                put_s3_res.clean_up_created_s3_object_when_update_dynamodb_item_failed(
                    s3_client=s3_client,
                )
            raise e

    @classmethod
    def delete_large_attribute_item(
        cls: T.Union[T.Type["Model"], T.Type["LargeAttributeMixin"]],
        s3_client: T.Union["S3Client", T.Dict[str, "S3Client"]],
        pk: T.Union[str, int],
        sk: T.Optional[T.Union[str, int]],
        attributes: T.Optional[T.List[str]] = None,
        clean_up_when_succeeded: bool = True,
        _error: T.Optional[Exception] = None,
    ):
        """
        Wrap the DynamoDB delete_item and S3 delete_object operation in a transaction.

        :param s3_client: ``boto3.client("s3")`` object.
        :param pk: hash key value of the DynamoDB item.
        :param sk: range key value if your DynamoDB table has range key, otherwise
            use None.
        :param attributes: list of large attribute names to delete. This is required
            when clean_up_when_succeeded is True. If clean_up_when_succeeded is False,
            this parameter has no effect.
        :param clean_up_when_succeeded: if True, the corresponding S3 object will
            deleted after DynamoDB item been deleted.

        """
        # note: the pynamodb.Model.delete() method doesn't have ``return_values``
        # parameter, we can't get the old model after delete it. So we have to
        # manually get the old model for cleaning up S3 object when deletion succeeded.
        if clean_up_when_succeeded:
            if attributes is None:
                raise ValueError(
                    "You must provide the list of large attribute "
                    "to delete their corresponding S3 objects"
                )
            attributes_to_get = list(attributes)
            attributes_to_get.append(cls._hash_keyname)
            if cls._range_keyname:  # pragma: no cover
                attributes_to_get.append(cls._range_keyname)
            old_model = cls.get(
                hash_key=pk,
                range_key=sk,
                attributes_to_get=attributes_to_get,
            )
        else:
            old_model = cls.make_one(hash_key=pk, range_key=sk)
        old_model.delete()

        if clean_up_when_succeeded:
            s3_uri_list = list()
            for attr_name in attributes:
                s3_uri = getattr(old_model, attr_name)
                s3_uri_list.append(s3_uri)
            batch_delete_s3_objects(s3_client, s3_uri_list)

    @classmethod
    def clean_up_dangling_s3_objects(
        cls: T.Union[T.Type["Model"], T.Type["LargeAttributeMixin"]],
        s3_client: T.Union["S3Client", T.Dict[str, "S3Client"]],
        attributes: T.List[str],
        bucket: str,
        prefix: str,
        expire: int,
    ) -> T.List[str]:  # pragma: no cover
        """
        Clean up dangling S3 objects. A dangling S3 object is an object that is not
        referenced by any DynamoDB item.

        :param s3_client: ``boto3.client("s3")`` object.
        :param attributes: the list of large attribute names.
        :param bucket: S3 bucket name.
        :param prefix: S3 prefix to scan.
        :param expire: we don't delete S3 object that is modified with in
            the last `expire` seconds, even it is dangling.
        """
        # get all existing large attribute S3 URIs
        if len(attributes) == 0:
            raise ValueError
        attr = attributes[0]
        condition = getattr(cls, attr).exists()
        for attr in attributes[1:]:
            condition |= getattr(cls, attr).exists()

        existing_large_attribute_s3_uri_set = set()
        for model in cls.scan(
            filter_condition=condition,
            attributes_to_get=attributes,
        ):
            for attr in attributes:
                value = getattr(model, attr)
                if value is not None:
                    existing_large_attribute_s3_uri_set.add(value)

        # if an S3 object is not in the existing_large_attribute_s3_uri_set,
        # then it is a dangling S3 object.
        now = datetime.utcnow()
        threshold = now - timedelta(seconds=expire)
        paginator = s3_client.get_paginator("list_objects_v2")
        response_iterator = paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
            PaginationConfig={
                "PageSize": 1000,
            },
        )
        to_delete_s3_uri_list = list()
        for response in response_iterator:
            for dct in response.get("Contents", []):
                s3_key = dct["Key"]
                last_modified = dct["LastModified"]
                s3_uri = join_s3_uri(bucket, s3_key)
                if (s3_uri not in existing_large_attribute_s3_uri_set) and (
                    last_modified < threshold
                ):
                    to_delete_s3_uri_list.append(s3_uri)
        batch_delete_s3_objects(s3_client, to_delete_s3_uri_list)
        return to_delete_s3_uri_list
