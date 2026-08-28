"""SMART on FHIR OAuth 2.0 service with PKCE and server-side grant issuance."""

from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rbac import Role, ROLE_SCOPE_MAP
from app.core.security import issue_access_token, verify_access_token_signature
from app.models.token_grant import OAuthAuthorizationCode, TokenGrant


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _validate_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method != "S256":
        return False
    return secrets.compare_digest(_pkce_challenge(code_verifier), code_challenge)


def _scopes_from_request(scope_string: str) -> list[str]:
    return [s for s in scope_string.split() if s.strip()]


def _roles_for_scopes(scopes: list[str]) -> list[str]:
    """Assign server-side roles based on requested scopes — never client-supplied."""
    assigned: set[str] = set()
    scope_set = set(scopes)
    for role, role_scopes in ROLE_SCOPE_MAP.items():
        if scope_set.intersection(role_scopes):
            assigned.add(role.value)
    if not assigned:
        assigned.add(Role.CLINICIAN.value)
    return sorted(assigned)


class OAuthService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_authorization_code(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str,
        state: str,
        code_challenge: str,
        code_challenge_method: str,
        subject_id: str,
        patient_id: str | None = None,
        launch: str | None = None,
    ) -> str:
        scopes = _scopes_from_request(scope)
        if "launch/patient" in scopes or "launch" in scopes:
            if not patient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="launch scope requires patient context",
                )
        if any(s.startswith("patient/") for s in scopes) and not patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient/*. scopes require patient binding",
            )

        code = secrets.token_urlsafe(32)
        auth_code = OAuthAuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            scopes=scopes,
            roles=_roles_for_scopes(scopes),
            subject_id=subject_id,
            patient_id=patient_id,
            launch_context=launch,
            state=state,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        self._db.add(auth_code)
        await self._db.flush()
        return code

    def build_redirect_uri(self, redirect_uri: str, code: str, state: str) -> str:
        params = urlencode({"code": code, "state": state})
        separator = "&" if "?" in redirect_uri else "?"
        return f"{redirect_uri}{separator}{params}"

    async def exchange_authorization_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        code_verifier: str,
    ) -> dict:
        result = await self._db.execute(
            select(OAuthAuthorizationCode).where(OAuthAuthorizationCode.code == code)
        )
        auth_code = result.scalar_one_or_none()
        if auth_code is None:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        if auth_code.consumed:
            raise HTTPException(status_code=400, detail="Authorization code already used")
        if auth_code.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=400, detail="Authorization code expired")
        if auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri:
            raise HTTPException(status_code=400, detail="Client or redirect_uri mismatch")
        if not _validate_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
            raise HTTPException(status_code=400, detail="PKCE verification failed")

        auth_code.consumed = True
        token, jti, expires_at = issue_access_token(auth_code.subject_id)
        grant = TokenGrant(
            jti=jti,
            subject_id=auth_code.subject_id,
            client_id=client_id,
            scopes=auth_code.scopes,
            roles=auth_code.roles,
            patient_id=auth_code.patient_id,
            launch_context=auth_code.launch_context,
            expires_at=expires_at,
        )
        self._db.add(grant)
        await self._db.flush()

        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(auth_code.scopes),
            "patient": auth_code.patient_id,
        }

    async def introspect_token(self, token: str) -> dict:
        try:
            claims = verify_access_token_signature(token)
        except Exception:
            return {"active": False}

        jti = claims.get("jti")
        result = await self._db.execute(select(TokenGrant).where(TokenGrant.jti == jti))
        grant = result.scalar_one_or_none()
        if grant is None or grant.revoked or grant.expires_at < datetime.now(UTC):
            return {"active": False}

        return {
            "active": True,
            "sub": grant.subject_id,
            "client_id": grant.client_id,
            "scope": " ".join(grant.scopes),
            "patient": grant.patient_id,
            "exp": int(grant.expires_at.timestamp()),
            "jti": grant.jti,
        }

    async def revoke_token(self, token: str) -> None:
        try:
            claims = verify_access_token_signature(token)
        except Exception:
            return
        jti = claims.get("jti")
        result = await self._db.execute(select(TokenGrant).where(TokenGrant.jti == jti))
        grant = result.scalar_one_or_none()
        if grant:
            grant.revoked = True
            await self._db.flush()

    async def resolve_grant_by_jti(self, jti: str) -> TokenGrant | None:
        result = await self._db.execute(select(TokenGrant).where(TokenGrant.jti == jti))
        grant = result.scalar_one_or_none()
        if grant is None or grant.revoked or grant.expires_at < datetime.now(UTC):
            return None
        return grant
