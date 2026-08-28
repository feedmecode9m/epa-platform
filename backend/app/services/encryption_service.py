"""PHI encryption service placeholder."""

import json

from app.core.encryption import PHIEncryptionService


class EncryptionService:
    """Wrapper around PHIEncryptionService for field-level encryption."""

    def __init__(self, phi: PHIEncryptionService) -> None:
        self._phi = phi

    def encrypt_field(self, value: str) -> str:
        return self._phi.encrypt(value)

    def decrypt_field(self, ciphertext: str) -> str:
        return self._phi.decrypt(ciphertext)

    def encrypt_json(self, data: dict) -> str:
        return self._phi.encrypt(json.dumps(data))

    def decrypt_json(self, ciphertext: str) -> dict:
        return json.loads(self._phi.decrypt(ciphertext))
