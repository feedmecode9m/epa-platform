"""FastAPI dependency injection — DB sessions, auth, RBAC."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_policy import AuthPolicyEngine, AuthorizedContext, auth_policy
from app.core.database import get_db
from app.core.envelope_encryption import EnvelopeEncryptionService, envelope_encryption
from app.core.security import TokenValidationError, verify_access_token_signature
from app.services.oauth_service import OAuthService

security_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """Request-scoped user resolved from server-side token grant — not JWT claims."""

    def __init__(self, ctx: AuthorizedContext):
        self._ctx = ctx
        self.id = ctx.subject_id
        self.jti = ctx.jti
        self.scopes = list(ctx.scopes)
        self.roles = list(ctx.roles)
        self.patient_id = ctx.patient_id
        self.fhir_user = ctx.fhir_user

    def has_permission(self, permission: str) -> bool:
        return self._ctx.has_permission(permission)

    def has_scope(self, scope: str) -> bool:
        return self._ctx.has_scope(scope)

    def assert_patient_access(self, resource_patient_id: str | None) -> None:
        self._ctx.assert_patient_access(resource_patient_id)


async def _resolve_authorized_context(
    credentials: HTTPAuthorizationCredentials,
    db: AsyncSession,
) -> AuthorizedContext:
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = verify_access_token_signature(credentials.credentials)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    jti = claims.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Token missing jti claim")

    oauth = OAuthService(db)
    grant = await oauth.resolve_grant_by_jti(jti)
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token grant not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthorizedContext.from_grant(grant)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    ctx = await _resolve_authorized_context(credentials, db)
    ctx.assert_launch_scope_valid()
    return CurrentUser(ctx)


def require_permission(permission: str):
    async def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        auth_policy.authorize_permission(user._ctx, permission)
        return user

    return checker


def require_scope(scope: str):
    async def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        auth_policy.authorize_scope(user._ctx, scope)
        return user

    return checker


def require_scope_and_permission(scope: str, permission: str):
    async def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        auth_policy.authorize_scope_and_permission(user._ctx, scope, permission)
        return user

    return checker


async def get_request_id(
    x_request_id: Annotated[str | None, Header()] = None,
) -> UUID | None:
    if x_request_id:
        try:
            return UUID(x_request_id)
        except ValueError:
            pass
    return None


DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]


def get_envelope_encryption() -> EnvelopeEncryptionService:
    return envelope_encryption


EnvelopeEncryptionDep = Annotated[EnvelopeEncryptionService, Depends(get_envelope_encryption)]
