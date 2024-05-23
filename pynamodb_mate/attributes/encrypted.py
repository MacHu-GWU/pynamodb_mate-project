# -*- coding: utf-8 -*-

"""
Implement Client Side Encryption Attribute for Unicode, Binary, Numbers and
Json data.
"""

import typing as T
import json
import typing

from pynamodb.attributes import BinaryAttribute

from ..cipher import str_to_key, BaseCipher, AesEcbCipher, AesCtrCipher


class SymmetricEncryptedAttribute(BinaryAttribute):
    """
    SymmetricEncryptedAttribute will encrypt your data in binary format
     before sending to DynamoDB.
    """

    def __init__(
        self,
        encryption_key: str,
        determinative: bool = True,
        hash_key: bool = False,
        range_key: bool = False,
        null: T.Optional[bool] = None,
        default: T.Optional[T.Callable] = None,
        default_for_new: T.Optional[T.Callable] = None,
        attr_name: T.Optional[str] = None,
        legacy_encoding: bool = False,
    ):
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            null=null,
            default=default,
            default_for_new=default_for_new,
            attr_name=attr_name,
            legacy_encoding=legacy_encoding,
        )
        self.encryption_key = encryption_key
        self.determinative = determinative
        self._key: T.Optional[bytes] = None
        self._cipher: T.Optional[BaseCipher] = None

    @property
    def key(self) -> bytes:
        if self._key is None:
            self._key = str_to_key(self.encryption_key)
        return self._key

    @property
    def cipher(self) -> BaseCipher:
        """
        :rtype: SymmtricCipher
        """
        if self._cipher is None:
            if self.determinative is True:
                self._cipher = AesEcbCipher(key=self.key)
            elif self.determinative is False:
                self._cipher = AesCtrCipher(key=self.key)
            else:  # pragma: no cover
                raise ValueError
        return self._cipher

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

    def serialize(self, value: T.Any) -> bytes:
        return self.cipher.encrypt(self.user_serializer(value))

    def deserialize(self, value: bytes) -> T.Any:
        return self.user_deserializer(self.cipher.decrypt(value))


class EncryptedUnicodeAttribute(SymmetricEncryptedAttribute):
    """
    Encrypted Unicode Attribute.
    """

    def user_serializer(self, value: str) -> bytes:
        return value.encode("utf-8")

    def user_deserializer(self, value: bytes) -> str:
        return value.decode("utf-8")


class EncryptedBinaryAttribute(SymmetricEncryptedAttribute):
    def user_serializer(self, value: bytes) -> bytes:
        return value

    def user_deserializer(self, value: bytes) -> bytes:
        return value


class EncryptedNumberAttribute(SymmetricEncryptedAttribute):
    """
    Encrypted Number Attribute.
    """

    def user_serializer(self, value: typing.Union[int, float]) -> bytes:
        return json.dumps(value).encode("ascii")

    def user_deserializer(self, value: bytes) -> typing.Union[int, float]:
        return json.loads(value.decode("ascii"))


class EncryptedJsonDictAttribute(SymmetricEncryptedAttribute):
    """
    Encrypted JSON data Attribute.
    """

    def user_serializer(self, value: dict) -> bytes:
        return json.dumps(value).encode("utf-8")

    def user_deserializer(self, value: bytes) -> dict:
        return json.loads(value.decode("utf-8"))
