"""Mock KMS provider and envelope encryption key management."""

from __future__ import annotations

import base64
import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


@dataclass(frozen=True)
class EncryptedDEK:
    """Data Encryption Key wrapped by a Customer Master Key (CMK)."""

    cmk_key_id: str
    encrypted_dek: str  # base64
    dek_version: int = 1


class KMSProvider(ABC):
    @abstractmethod
    def generate_data_key(self, cmk_key_id: str) -> tuple[bytes, EncryptedDEK]:
        """Return (plaintext DEK, encrypted DEK blob)."""

    @abstractmethod
    def decrypt_data_key(self, encrypted_dek: EncryptedDEK) -> bytes:
        """Unwrap an encrypted DEK using the CMK."""


class MockKMSProvider(KMSProvider):
    """Development KMS substitute.

    CMK is derived deterministically from ``PHI_ENCRYPTION_KEY_ID`` so encrypted
    DEKs survive process restarts in non-production environments. Replace with
    AWS KMS / HashiCorp Vault in production.
    """

    def __init__(self, master_seed: str | None = None):
        seed = master_seed or settings.PHI_ENCRYPTION_KEY_ID
        self._cmk = hashlib.sha256(seed.encode()).digest()

    def _wrap(self, dek: bytes, cmk_key_id: str) -> EncryptedDEK:
        nonce = os.urandom(12)
        aead = AESGCM(self._cmk)
        wrapped = aead.encrypt(nonce, dek, cmk_key_id.encode())
        blob = base64.b64encode(nonce + wrapped).decode("ascii")
        return EncryptedDEK(cmk_key_id=cmk_key_id, encrypted_dek=blob)

    def _unwrap(self, encrypted_dek: EncryptedDEK) -> bytes:
        raw = base64.b64decode(encrypted_dek.encrypted_dek)
        nonce, ciphertext = raw[:12], raw[12:]
        aead = AESGCM(self._cmk)
        return aead.decrypt(nonce, ciphertext, encrypted_dek.cmk_key_id.encode())

    def generate_data_key(self, cmk_key_id: str) -> tuple[bytes, EncryptedDEK]:
        dek = os.urandom(32)
        return dek, self._wrap(dek, cmk_key_id)

    def decrypt_data_key(self, encrypted_dek: EncryptedDEK) -> bytes:
        return self._unwrap(encrypted_dek)


_kms_provider: KMSProvider | None = None


def get_kms_provider() -> KMSProvider:
    global _kms_provider
    if _kms_provider is None:
        _kms_provider = MockKMSProvider()
    return _kms_provider
