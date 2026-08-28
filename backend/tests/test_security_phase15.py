"""Unit tests for Phase 1.5 security hardening."""

import base64
import hashlib
import json

import pytest

from app.core.auth_policy import AuthorizedContext
from app.core.envelope_encryption import EnvelopeEncryptionService
from app.core.security import build_access_token_claims, issue_access_token, verify_access_token_signature
from app.core.jwks import get_jwks_manager
from app.models.token_grant import TokenGrant
from app.services.audit_chain import compute_audit_hash, GENESIS_HASH
from app.services.oauth_service import _pkce_challenge, _validate_pkce


def test_jwt_payload_excludes_roles_and_scopes():
    claims = build_access_token_claims("user-123")
    assert "roles" not in claims
    assert "scope" not in claims
    assert claims["sub"] == "user-123"
    assert "jti" in claims


def test_rs256_jwt_verification_roundtrip():
    get_jwks_manager.cache_clear()
    token, jti, _expires = issue_access_token("user-456")
    decoded = verify_access_token_signature(token)
    assert decoded["sub"] == "user-456"
    assert decoded["jti"] == jti


def test_forged_roles_in_jwt_are_ignored_by_policy_engine():
    get_jwks_manager.cache_clear()
    manager = get_jwks_manager()
    malicious_claims = build_access_token_claims("attacker")
    malicious_claims["roles"] = ["admin"]
    malicious_claims["scope"] = "system/*.write"
    token = manager.sign_jwt(malicious_claims)

    decoded = manager.verify_jwt(token)
    assert decoded["sub"] == "attacker"

    grant = TokenGrant(
        jti=decoded["jti"],
        subject_id="attacker",
        scopes=["patient/Patient.read"],
        roles=["readonly_auditor"],
        expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC)
        + __import__("datetime").timedelta(minutes=5),
    )
    ctx = AuthorizedContext.from_grant(grant)
    assert not ctx.has_permission("prior_auth:create")
    assert not ctx.has_scope("system/*.write")


def test_pkce_s256_validation():
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    challenge = _pkce_challenge(verifier)
    assert _validate_pkce(verifier, challenge, "S256")
    assert not _validate_pkce("wrong", challenge, "S256")


def test_audit_hash_chain_detects_tampering():
    event_a = {"id": "1", "action": "GET /api/v1/test", "outcome": "success"}
    hash_a = compute_audit_hash(GENESIS_HASH, event_a)
    event_b = {"id": "2", "action": "GET /api/v1/test", "outcome": "success"}
    hash_b = compute_audit_hash(hash_a, event_b)
    tampered = compute_audit_hash(GENESIS_HASH, event_b)
    assert hash_b != tampered


def test_envelope_encryption_roundtrip():
    service = EnvelopeEncryptionService()
    stored = service.encrypt_patient_ssn("123-45-6789")
    assert stored["encrypted_value"] != "123-45-6789"
    assert stored["encrypted_dek"] != stored["encrypted_value"]
    plaintext = service.decrypt_patient_ssn(stored)
    assert plaintext == "123-45-6789"


def test_patient_context_mismatch_denied():
    grant = TokenGrant(
        jti="test-jti",
        subject_id="clinician-1",
        scopes=["launch/patient", "patient/Claim.read"],
        roles=["clinician"],
        patient_id="Patient/A",
        expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC)
        + __import__("datetime").timedelta(minutes=5),
    )
    ctx = AuthorizedContext.from_grant(grant)
    with pytest.raises(Exception):
        ctx.assert_patient_access("Patient/B")
