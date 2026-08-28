"""JWT token issuance and cryptographic validation (RS256 + JWKS).

JWTs carry identity claims (``sub``, ``jti``) only. Scopes and roles are
stored in ``TokenGrant`` and resolved server-side at request time.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError

from app.core.config import settings
from app.core.jwks import get_jwks_manager


class TokenValidationError(ValueError):
    pass


def build_access_token_claims(subject_id: str, jti: str | None = None) -> dict[str, Any]:
    """Build minimal JWT claims — no roles or scopes in the payload."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "sub": subject_id,
        "jti": jti or str(uuid4()),
        "iss": settings.OAUTH_ISSUER,
        "aud": settings.OAUTH_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }


def issue_access_token(subject_id: str, jti: str | None = None) -> tuple[str, str, datetime]:
    """Sign an RS256 access token. Returns (token, jti, expires_at)."""
    claims = build_access_token_claims(subject_id, jti)
    token = get_jwks_manager().sign_jwt(claims)
    expires_at = datetime.fromtimestamp(claims["exp"], tz=UTC)
    return token, claims["jti"], expires_at


def verify_access_token_signature(token: str) -> dict[str, Any]:
    """Verify JWT signature and standard claims via local JWKS public key."""
    try:
        return get_jwks_manager().verify_jwt(token)
    except JWTError as exc:
        raise TokenValidationError("Invalid or expired token") from exc


def parse_scopes(scope_string: str) -> list[str]:
    return [s.strip() for s in scope_string.split() if s.strip()]
