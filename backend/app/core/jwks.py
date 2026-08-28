"""RSA key pair management and JWKS publication for RS256 JWT signing."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from app.core.config import settings


def _int_to_base64url(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class JWKSManager:
    """Manages RS256 signing keys and JWKS document generation."""

    def __init__(self, private_key_pem: bytes | None = None, key_id: str | None = None):
        self.key_id = key_id or settings.JWT_KEY_ID
        if private_key_pem:
            self._private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        else:
            private_path = Path(settings.JWT_PRIVATE_KEY_PATH)
            if private_path.exists():
                self._private_key = serialization.load_pem_private_key(
                    private_path.read_bytes(), password=None
                )
            else:
                self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        public_numbers = self._private_key.public_key().public_numbers()
        self._private_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self._public_pem = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self._jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": self.key_id,
                    "use": "sig",
                    "alg": "RS256",
                    "n": _int_to_base64url(public_numbers.n),
                    "e": _int_to_base64url(public_numbers.e),
                }
            ]
        }

    @property
    def public_pem(self) -> bytes:
        return self._public_pem

    def jwks_document(self) -> dict[str, Any]:
        return self._jwks

    def sign_jwt(self, claims: dict[str, Any]) -> str:
        headers = {"kid": self.key_id, "alg": "RS256", "typ": "JWT"}
        return jwt.encode(
            claims,
            self._private_pem,
            algorithm="RS256",
            headers=headers,
        )

    def verify_jwt(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            token,
            self._public_pem,
            algorithms=["RS256"],
            audience=settings.OAUTH_AUDIENCE,
            issuer=settings.OAUTH_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti"]},
        )


@lru_cache
def get_jwks_manager() -> JWKSManager:
    return JWKSManager()
