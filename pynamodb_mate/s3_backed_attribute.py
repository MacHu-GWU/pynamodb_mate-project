# -*- coding: utf-8 -*-

"""
Implement S3 Backed Binary and Unicode Attribute.

Since the content of big Binary or Unicode are not stored in DynamoDB, we
cannot use custom attriubte ``pynamodb.attributes.Attribute`` to implement it.
"""

import zlib
from base64 import b64encode, b64decode

from pynamodb.models import Model
from six import string_types

try:
    import typing
except:
    pass


def s3_key_safe_b64encode(text):
    return b64encode(text.encode("utf-8")).decode("utf-8").replace("=", "")


def s3_key_safe_b64decode(text):
    div, mod = divmod(len(text), 4)
    if mod != 0:
        text = text + "=" * (4 - mod)
    return b64decode(text.encode("utf-8")).decode("utf-8")


def parse_s3_uri(s3_uri):
    chunks = s3_uri.split("/", 3)
    bucket = chunks[2]
    key = chunks[3]
    return bucket, key


class BaseS3BackedAttribute(object):
    """
    Implement S3 relative operation for each attribute.

    :type s3_uri_getter: typing.Union[str, typing.Callable]
    :param s3_uri_getter: str or callable function, it takes the pynamodb orm
        object as input, returns the S3 URI string for this s3 backed attribute.
    """

    def __init__(self, s3_uri_getter, compress=False, name=None):
        self.s3_uri_getter = s3_uri_getter
        if isinstance(s3_uri_getter, string_types):
            self.s3_uri_getter_real = lambda obj: getattr(obj, s3_uri_getter)
        elif callable(s3_uri_getter):
            self.s3_uri_getter_real = s3_uri_getter
        else:
            raise Exception
        self.compress = compress
        self.name = name

    def serialize(self, data):
        raise NotImplementedError

    def deserialize(self, data):
        raise NotImplementedError

    def set_to(self, data):
        return (self, data)

    def head_object(self, model_obj):
        s3_uri = self.s3_uri_getter_real(model_obj)
        bucket, key = parse_s3_uri(s3_uri)
        return model_obj.get_s3_client().head_object(Bucket=bucket, Key=key)

    def _put_binary_data(self, model_obj, data):
        """
        Write binary data as it is to s3.

        :type model_obj: S3BackedMixin
        :type data: bytes
        """
        s3_uri = self.s3_uri_getter_real(model_obj)
        bucket, key = parse_s3_uri(s3_uri)
        res = model_obj.get_s3_client().put_object(
            Bucket=bucket, Key=key, Body=data)
        return res

    def put_object(self, model_obj, data):
        """
        :type model_obj: S3BackedMixin
        """
        if self.compress:
            body = zlib.compress(self.serialize(data))
        else:
            body = self.serialize(data)
        return self._put_binary_data(model_obj, body)

    def _read_binary_data(self, model_obj):
        """
        Read binary data as it is from s3

        :type model_obj: S3BackedMixin
        """
        s3_uri = self.s3_uri_getter_real(model_obj)
        bucket, key = parse_s3_uri(s3_uri)
        res = model_obj.get_s3_client().get_object(
            Bucket=bucket, Key=key)
        return res["Body"].read()

    def read_data(self, model_obj):
        """
        :return:
        """
        if self.compress:
            return self.deserialize(zlib.decompress(self._read_binary_data(model_obj)))
        else:
            return self.deserialize(self._read_binary_data(model_obj))

    def delete_object(self, model_obj):
        """

        :type model_obj: S3BackedMixin
        """
        s3_uri = self.s3_uri_getter_real(model_obj)
        bucket, key = parse_s3_uri(s3_uri)
        res = model_obj.get_s3_client().delete_object(Bucket=bucket, Key=key)
        return res


class S3BackedBinaryAttribute(BaseS3BackedAttribute):
    def serialize(self, data):
        return data

    def deserialize(self, data):
        return data


class S3BackedUnicodeAttribute(BaseS3BackedAttribute):
    def serialize(self, data):
        return data.encode("utf-8")

    def deserialize(self, data):
        return data.decode("utf-8")


class S3BackedMixin(object):  # type: typing.Type[Model]
    _s3_client = None
    _s3_backed_attr_mapper = None
    _s3_backed_value_mapper = None

    @classmethod
    def get_s3_backed_attr_mapper(cls):
        """
        :type cls: Model

        :rtype: dict
        """
        if cls._s3_backed_attr_mapper is None:
            cls._s3_backed_attr_mapper = dict()
            for attr, value in cls.__dict__.items():
                try:
                    if isinstance(value, BaseS3BackedAttribute):
                        value.name = attr
                        cls._s3_backed_attr_mapper[attr] = value
                except Exception as e:
                    pass
        return cls._s3_backed_attr_mapper

    @classmethod
    def get_s3_client(cls):
        """
        :type cls: Model
        """
        if cls._s3_client is None:
            pynamodb_connection = cls._get_connection().connection
            cls._s3_client = pynamodb_connection.session.create_client(
                "s3", pynamodb_connection.region)
        return cls._s3_client

    def atomic_save(self,
                    condition=None,
                    s3_backed_data=None):
        """
        An ``atomic`` save operation for multiple S3 backed attribute.

        :type self: typing.Union[Model, S3BackedMixin]

        :type s3_backed_data: List[BaseS3BackedAttribute.set_to(data)]
        :param s3_backed_data: example ``[page.html_content.set_to("<html> ... </html>"), page.image_content.set_to(b"...")]``
        """
        if s3_backed_data is None:
            s3_backed_data = list()

        saved_data_list = list()

        for s3_backed_attr, data in s3_backed_data:
            try:
                s3_backed_attr.put_object(self, data)
                saved_data_list.append((s3_backed_attr, data))
            # if any of s3.put_object failed, roll back and skip dynamodb.put_item
            except Exception as put_object_error:
                for s3_backed_attr, data in saved_data_list:
                    s3_backed_attr.delete_object(self)
                raise put_object_error

        try:
            res = self.save(condition=condition)
            del saved_data_list
            return res
        except Exception as dynamodb_save_error:  # delete saved s3 object if dynamodb write operation failed
            for s3_backed_attr, data in saved_data_list:
                s3_backed_attr.delete_object(self)
            del saved_data_list
            raise dynamodb_save_error

    def atomic_update(self,
                      actions=None,
                      condition=None,
                      s3_backed_data=None):
        """
        An ``atomic`` update operation for multiple S3 backed attribute.

        :type self: typing.Union[Model, S3BackedMixin]

        :type s3_backed_data: List[BaseS3BackedAttribute.set_to(data)]
        :param s3_backed_data: example ``[page.html_content.set_to("<html> ... </html>"), page.image_content.set_to(b"...")]``
        """
        if s3_backed_data is None:
            s3_backed_data = list()

        previous_data_list = list()
        for s3_backed_attr, data in s3_backed_data:
            try:
                previous_data_list.append(
                    (
                        s3_backed_attr,
                        s3_backed_attr._read_binary_data(self)
                    )
                )
                s3_backed_attr.put_object(self, data)
            # if any of s3.put_object failed, roll back and skip dynamodb.put_item
            except Exception as put_object_error:
                for s3_backed_attr, data in previous_data_list:
                    s3_backed_attr.put_object(self, data)
                raise put_object_error

        if actions is not None:
            return self.update(actions=actions, condition=condition)

    def atomic_delete(self,
                      condition=None):
        """
        An ``atomic`` delete operation for multiple S3 backed attribute.

        :type self: typing.Union[Model, S3BackedMixin]
        """
        self.delete(condition=condition)
        for attr, value in self.get_s3_backed_attr_mapper().items():
            # check if the s3 object exists, if exists, delete it
            try:
                value.head_object(self)
                value.delete_object(self)
            except Exception as e:
                pass
