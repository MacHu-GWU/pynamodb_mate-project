# -*- coding: utf-8 -*-

import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from .helpers import bytes_to_base85str, base85str_to_bytes


def str_to_key(s: str) -> bytes:
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.digest()


class BaseCipher:
    def encrypt(self, b: bytes) -> bytes: # pragma: no cover
        raise NotImplementedError

    def decrypt(self, b: bytes) -> bytes: # pragma: no cover
        raise NotImplementedError


class AesEcbCipher(BaseCipher):
    """
    A determinative symmetric cipher. same input + same key = same output.
    """

    def __init__(self, key: bytes):
        self._key = key
        self._aes = AES.new(self._key, AES.MODE_ECB)

    def encrypt(self, b: bytes) -> bytes:
        return self._aes.encrypt(pad(b, AES.block_size))

    def decrypt(self, b: bytes) -> bytes:
        return unpad(self._aes.decrypt(b), AES.block_size)


class AesCtrCipher(BaseCipher):
    """
    A non-determinative symmetric cipher. same input + same key != same output.
    """

    def __init__(self, key: bytes):
        self._key = key

    def encrypt(self, b: bytes) -> bytes:
        aes = AES.new(self._key, AES.MODE_CTR)
        token = aes.encrypt(b)
        nonce = aes.nonce
        return json.dumps({
            "nonce": bytes_to_base85str(nonce),
            "token": bytes_to_base85str(token),
        }).encode("ascii")

    def decrypt(self, b: bytes) -> bytes:
        data = json.loads(b.decode("ascii"))
        token = base85str_to_bytes(data["token"])
        nonce = base85str_to_bytes(data["nonce"])
        aes = AES.new(self._key, AES.MODE_CTR, nonce=nonce)
        return aes.decrypt(token)
