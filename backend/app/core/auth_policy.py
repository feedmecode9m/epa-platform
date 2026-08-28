"""Centralized authorization policy engine.

Authorization decisions are derived from server-side token grants — never
from client-declared roles or scopes embedded in the JWT payload.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.rbac import Role, role_has_permission, roles_have_scope
from app.models.token_grant import TokenGrant


@dataclass(frozen=True)
class AuthorizedContext:
    """Resolved authorization context from a server-side token grant."""

    subject_id: str
    jti: str
    scopes: tuple[str, ...]
    roles: tuple[str, ...]
    patient_id: str | None
    fhir_user: str | None
    client_id: str | None
    launch_context: str | None

    @classmethod
    def from_grant(cls, grant: TokenGrant) -> AuthorizedContext:
        if grant.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
        return cls(
            subject_id=grant.subject_id,
            jti=grant.jti,
            scopes=tuple(grant.scopes or ()),
            roles=tuple(grant.roles or ()),
            patient_id=grant.patient_id,
            fhir_user=grant.fhir_user,
            client_id=grant.client_id,
            launch_context=grant.launch_context,
        )

    def has_scope(self, required_scope: str) -> bool:
        if required_scope in self.scopes:
            return True
        return roles_have_scope(list(self.roles), required_scope)

    def has_permission(self, permission: str) -> bool:
        for role_str in self.roles:
            try:
                if role_has_permission(Role(role_str), permission):
                    return True
            except ValueError:
                continue
        return False

    def assert_patient_access(self, resource_patient_id: str | None) -> None:
        """Enforce patient-scoped access for launch/patient contexts."""
        if resource_patient_id is None:
            return
        patient_scoped = any(
            s.startswith("patient/") or s in {"launch/patient", "launch"} for s in self.scopes
        )
        if not patient_scoped:
            return
        if self.patient_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient context required but not present in token grant",
            )
        if self.patient_id != resource_patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: patient context mismatch",
            )

    def assert_launch_scope_valid(self) -> None:
        """Validate SMART launch scope binding."""
        has_launch = "launch" in self.scopes or "launch/patient" in self.scopes
        if has_launch and self.patient_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="launch scope requires bound patient context",
            )


class AuthPolicyEngine:
    """Server-side policy evaluation against token grants."""

    def authorize_scope(self, ctx: AuthorizedContext, scope: str) -> None:
        if not ctx.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope: requires {scope}",
            )

    def authorize_permission(self, ctx: AuthorizedContext, permission: str) -> None:
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {permission}",
            )

    def authorize_scope_and_permission(
        self, ctx: AuthorizedContext, scope: str, permission: str
    ) -> None:
        ctx.assert_launch_scope_valid()
        self.authorize_scope(ctx, scope)
        self.authorize_permission(ctx, permission)


auth_policy = AuthPolicyEngine()
