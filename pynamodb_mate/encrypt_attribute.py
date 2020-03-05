# -*- coding: utf-8 -*-

"""
Implement Client Side Encryption Attribute for Unicode, Binary, Numbers and
Json data.
"""

from json import loads as json_loads, dumps as json_dumps

from pynamodb.attributes import UnicodeAttribute, BinaryAttribute
from windtalker import SymmetricCipher


class SymmetricEncryptedAttribute(object):
    encrypt_key = None  # type: str
    _cipher = None  # type: SymmetricCipher

    def get_cipher(self):
        """
        :rtype: SymmtricCipher
        """
        if self._cipher is None:
            if self.encrypt_key:
                self._cipher = SymmetricCipher(password=self.encrypt_key)
            else:
                raise Exception
        return self._cipher


class EncryptUnicodeAttribute(UnicodeAttribute, SymmetricEncryptedAttribute):
    def serialize(self, value):
        return self.get_cipher().encrypt_text(value)

    def deserialize(self, value):
        return self.get_cipher().decrypt_text(value)


class EncryptBinaryAttribute(BinaryAttribute, SymmetricEncryptedAttribute):
    def serialize(self, value):
        return self.get_cipher().encrypt_binary(value)

    def deserialize(self, value):
        return self.get_cipher().decrypt_binary(value)


class EncryptedNumberAttribute(UnicodeAttribute, SymmetricEncryptedAttribute):
    def serialize(self, value):
        return self.get_cipher().encrypt_text(json_dumps(value))

    def deserialize(self, value):
        return json_loads(self.get_cipher().decrypt_text(value))


class EncryptedJsonAttribute(EncryptedNumberAttribute):
    pass
