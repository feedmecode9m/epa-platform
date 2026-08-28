"""KMS-backed envelope encryption for PHI fields."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.core.kms import EncryptedDEK, KMSProvider, get_kms_provider


@dataclass(frozen=True)
class EnvelopeCiphertext:
    """Encrypted PHI payload with wrapped DEK for storage."""

    ciphertext: str  # base64(nonce + aes-gcm ciphertext)
    encrypted_dek: EncryptedDEK
    field_name: str
    algorithm: str = "AES-256-GCM"


class EnvelopeEncryptionService:
    """Encrypt PHI using per-operation DEKs wrapped by KMS CMK."""

    def __init__(self, kms: KMSProvider | None = None, cmk_key_id: str | None = None):
        self._kms = kms or get_kms_provider()
        self._cmk_key_id = cmk_key_id or settings.PHI_ENCRYPTION_KEY_ID

    def encrypt_field(self, plaintext: str, field_name: str) -> EnvelopeCiphertext:
        dek, encrypted_dek = self._kms.generate_data_key(self._cmk_key_id)
        aead = AESGCM(dek)
        nonce = os.urandom(12)
        aad = f"{field_name}:{self._cmk_key_id}".encode()
        ciphertext = aead.encrypt(nonce, plaintext.encode("utf-8"), aad)
        return EnvelopeCiphertext(
            ciphertext=base64.b64encode(nonce + ciphertext).decode("ascii"),
            encrypted_dek=encrypted_dek,
            field_name=field_name,
            algorithm=settings.PHI_ENCRYPTION_ALGORITHM,
        )

    def decrypt_field(self, envelope: EnvelopeCiphertext) -> str:
        dek = self._kms.decrypt_data_key(envelope.encrypted_dek)
        aead = AESGCM(dek)
        raw = base64.b64decode(envelope.ciphertext)
        nonce, ciphertext = raw[:12], raw[12:]
        aad = f"{envelope.field_name}:{self._cmk_key_id}".encode()
        plaintext = aead.decrypt(nonce, ciphertext, aad)
        return plaintext.decode("utf-8")

    def encrypt_patient_ssn(self, ssn: str) -> dict[str, Any]:
        """Demonstration: envelope-encrypt a sample PHI field for persistence."""
        envelope = self.encrypt_field(ssn, field_name="patient_ssn")
        return {
            "encrypted_value": envelope.ciphertext,
            "encrypted_dek": envelope.encrypted_dek.encrypted_dek,
            "cmk_key_id": envelope.encrypted_dek.cmk_key_id,
            "field_name": envelope.field_name,
            "algorithm": envelope.algorithm,
        }

    def decrypt_patient_ssn(self, stored: dict[str, Any]) -> str:
        envelope = EnvelopeCiphertext(
            ciphertext=stored["encrypted_value"],
            encrypted_dek=EncryptedDEK(
                cmk_key_id=stored["cmk_key_id"],
                encrypted_dek=stored["encrypted_dek"],
            ),
            field_name=stored["field_name"],
            algorithm=stored.get("algorithm", settings.PHI_ENCRYPTION_ALGORITHM),
        )
        return self.decrypt_field(envelope)


envelope_encryption = EnvelopeEncryptionService()
