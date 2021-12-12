# -*- coding: utf-8 -*-

"""
Implement Client Side Encryption Attribute for Unicode, Binary, Numbers and
Json data.
"""

import json
import typing
from json import loads as json_loads, dumps as json_dumps
from pynamodb.attributes import UnicodeAttribute, BinaryAttribute
from ..cipher import str_to_key, BaseCipher, AesEcbCipher, AesCtrCipher


class SymmetricEncryptedAttribute(object):
    encryption_key = None  # type: str
    determinative = None  # type: str

    _key = None  # type: bytes

    @property
    def key(self) -> bytes:
        if self._key is None:
            self._key = str_to_key(self.encryption_key)
        return self._key

    _cipher = None  # type: BaseCipher

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


class EncryptUnicodeAttribute(BinaryAttribute, SymmetricEncryptedAttribute):
    def serialize(self, value: str) -> bytes:
        return self.cipher.encrypt(value.encode("utf-8"))

    def deserialize(self, value: bytes) -> str:
        return self.cipher.decrypt(value).decode("utf-8")


class EncryptBinaryAttribute(BinaryAttribute, SymmetricEncryptedAttribute):
    def serialize(self, value: bytes) -> bytes:
        return self.cipher.encrypt(value)

    def deserialize(self, value: bytes) -> bytes:
        return self.cipher.decrypt(value)


class EncryptedNumberAttribute(BinaryAttribute, SymmetricEncryptedAttribute):
    def serialize(self, value: typing.Union[int, float]) -> bytes:
        return self.cipher.encrypt(json.dumps(value).encode("ascii"))

    def deserialize(self, value: bytes) -> typing.Union[int, float]:
        return json.loads(self.cipher.decrypt(value).decode("ascii"))


class EncryptedJsonAttribute(EncryptedNumberAttribute):
    pass
