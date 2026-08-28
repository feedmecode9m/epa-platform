"""Role-Based Access Control definitions and enforcement."""

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    CLINICIAN = "clinician"
    BILLING = "billing"
    PAYER_REVIEWER = "payer_reviewer"
    SYSTEM = "system"
    READONLY_AUDITOR = "readonly_auditor"


# Role → permitted SMART scopes
ROLE_SCOPE_MAP: dict[Role, set[str]] = {
    Role.ADMIN: {"system/*.read", "system/*.write", "system/AuditEvent.read"},
    Role.CLINICIAN: {
        "patient/Patient.read",
        "patient/Coverage.read",
        "user/CoverageEligibilityRequest.write",
        "user/Claim.write",
        "launch/patient",
    },
    Role.BILLING: {
        "patient/Patient.read",
        "patient/Coverage.read",
        "user/Claim.write",
    },
    Role.PAYER_REVIEWER: {
        "system/Claim.read",
        "system/Claim.write",
    },
    Role.SYSTEM: {"system/*.read", "system/*.write"},
    Role.READONLY_AUDITOR: {"system/AuditEvent.read"},
}

# Role → API endpoint permissions
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.CLINICIAN: {
        "prior_auth:create",
        "prior_auth:read",
        "eligibility:check",
        "patient:read",
    },
    Role.BILLING: {"prior_auth:create", "prior_auth:read", "eligibility:check"},
    Role.PAYER_REVIEWER: {"prior_auth:read", "prior_auth:update_status"},
    Role.SYSTEM: {"prior_auth:create", "prior_auth:read", "eligibility:check"},
    Role.READONLY_AUDITOR: {"audit:read"},
}


def role_has_permission(role: Role, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms


def roles_have_scope(roles: list[str], required_scope: str) -> bool:
    for role_str in roles:
        try:
            role = Role(role_str)
        except ValueError:
            continue
        scopes = ROLE_SCOPE_MAP.get(role, set())
        for scope in scopes:
            if scope == required_scope:
                return True
            if scope.endswith("/*"):
                prefix = scope[:-1]
                if required_scope.startswith(prefix):
                    return True
    return False
