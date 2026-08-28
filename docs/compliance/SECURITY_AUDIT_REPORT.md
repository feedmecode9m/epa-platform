# Security Audit Report — Phase 1

**Auditor**: `security-auditor` subagent  
**Date**: 2026-08-28  
**Scope**: OpenAPI specification, core security modules, middleware, ORM models  
**Framework**: HIPAA Security Rule (45 CFR §164.308–314), SMART on FHIR v2.0.1, OAuth 2.0 / OIDC best practices

---

## Executive Summary

Phase 1 artifacts demonstrate **correct security architecture intent** (RBAC definitions, PHI encryption service, hash-chained audit model, SMART OAuth specification). Implementation is **scaffold-only** and contains multiple **CRITICAL** vulnerabilities that would permit PHI exposure, privilege escalation, and non-durable audit trails if deployed with real data.

**Overall Risk Rating**: **CRITICAL — Not suitable for PHI processing**

The platform must not receive, store, or transmit real PHI until all CRITICAL findings and applicable HIGH findings are remediated and independently verified.

---

## Findings

| ID | Severity | Component | Finding | Recommendation |
|----|----------|-----------|---------|----------------|
| SEC-C01 | **CRITICAL** | `middleware/audit.py` | Audit events are computed in-process only (`# TODO: Persist to append-only audit_log table`). Hash chain state lives in module-global `_last_audit_hash` and is lost on restart or worker recycle. HIPAA §164.312(b) requires durable, reviewable audit trails. | Persist every audit event to `audit_logs` synchronously or via guaranteed-delivery queue before returning response. Rehydrate chain head from DB on startup. Add monitoring for write failures. |
| SEC-C02 | **CRITICAL** | `core/encryption.py` | `PHIEncryptionService` defaults to `os.urandom(32)` when no key is supplied. Key is non-deterministic across restarts — all encrypted PHI becomes permanently unrecoverable. No KMS/HSM integration despite `PHI_ENCRYPTION_KEY_ID` setting. | Integrate envelope encryption with AWS KMS / Azure Key Vault / GCP Cloud KMS. Load DEK at startup; implement key rotation with re-encryption jobs. Fail fast in production if KMS is unreachable. |
| SEC-C03 | **CRITICAL** | `api/v1/endpoints/oauth.py` | OAuth/SMART endpoints (`/oauth/authorize`, `/oauth/token`, `/oauth/introspect`, `/oauth/revoke`) are non-functional placeholders returning static JSON. No authorization code flow, PKCE validation, token issuance, or client authentication is implemented. | Implement full SMART on FHIR authorization code + PKCE flow before any protected endpoint accepts traffic. Block deployment if OAuth handlers return placeholder responses. |
| SEC-C04 | **CRITICAL** | `core/security.py`, `core/deps.py` | JWT `roles` and `scope` claims are trusted directly from the bearer token without server-side lookup against `User.roles` or authorized scope grants. An attacker with a valid or forged token can embed `roles: ["admin"]` or arbitrary SMART scopes. `has_scope()` returns `True` if scope appears in token regardless of role assignment. | Resolve roles and scopes server-side at token issuance only; never trust client-supplied role claims. At request time, validate scopes against issued grant record. Remove `roles` from JWT or sign via dedicated token service with strict claim policy. |
| SEC-C05 | **CRITICAL** | `core/config.py`, `core/security.py` | Default `JWT_SECRET_KEY` is a known placeholder string. HS256 symmetric signing with a weak/default secret enables token forgery and full API impersonation. No startup validation rejects default secrets in production. | Require secrets from a secrets manager (AWS Secrets Manager, Vault). Validate minimum entropy and reject defaults when `APP_ENV=production`. Rotate keys with overlap period and `kid` header support. |
| SEC-H01 | **HIGH** | `models/prior_auth.py`, `models/patient.py` | `PriorAuthorization.claim_resource` and `PatientRecord.fhir_resource` store full FHIR JSONB without application-layer encryption. These resources contain patient names, DOB, diagnoses, and medication data. Column-level encryption exists only for discrete `encrypted_*` fields on `PatientRecord`. | Encrypt JSONB PHI blobs before persistence using `PHIEncryptionService` with record-scoped AAD (e.g., `{table}:{id}`). Alternatively, store encrypted object references in S3 with SSE-KMS. Enable PostgreSQL TDE as defense-in-depth only. |
| SEC-H02 | **HIGH** | `models/audit_log.py`, `alembic/versions/0001_initial_placeholder.py` | Append-only audit enforcement is documented but not implemented. Migration placeholder has empty `upgrade()`. No PostgreSQL triggers, `REVOKE UPDATE/DELETE`, or row-level immutability. Audit records can be modified or deleted by any DB-privileged actor. | Deploy `prevent_audit_log_mutation()` trigger from migration comments. Revoke UPDATE/DELETE on `audit_logs` from application DB role. Restrict DBA access with break-glass logging. |
| SEC-H03 | **HIGH** | `core/deps.py`, `api/v1/endpoints/*`, `openapi/epa-platform-v1.yaml` | OpenAPI declares SMART OAuth scope requirements per endpoint (e.g., `user/Claim.write`), but route handlers enforce only internal permissions (`require_permission("prior_auth:create")`) — not SMART scopes via `require_scope()`. Scope enforcement gap between spec and implementation. | Enforce both permission **and** required SMART scope on every PHI endpoint. Align OpenAPI `security` blocks with runtime `require_scope()` dependencies. |
| SEC-H04 | **HIGH** | `core/deps.py`, `services/prior_auth.py` | No patient-context isolation. Patient-scoped tokens (`patient` claim) are not validated against resource `patient_id` on read/write. `get_status()` returns data without verifying the requesting user may access that patient. Cross-patient PHI access is possible. | Add `assert_patient_access(user, patient_id)` dependency. For `patient/*.read` scopes, restrict queries to `user.patient_id`. For `user/*` scopes, enforce organization/compartment boundaries. |
| SEC-H05 | **HIGH** | `core/security.py`, `oauth.py` | No refresh token implementation, rotation, or revocation store despite OpenAPI `refresh_token` grant and 7-day `JWT_REFRESH_TOKEN_EXPIRE_DAYS` config. No `jti` denylist. Compromised tokens remain valid until expiry. | Implement refresh token rotation (RFC 6749), one-time use refresh tokens, and RFC 7009 revocation backed by Redis/DB denylist. Bind refresh tokens to `client_id` and PKCE. |
| SEC-H06 | **HIGH** | `core/security.py`, OpenAPI | Access tokens use HS256 symmetric signing. SMART on FHIR implementations should expose RS256/ES256 JWTs with public JWKS (`/.well-known/jwks.json` referenced in OpenAPI but not implemented). Symmetric keys cannot be safely distributed to resource servers. | Migrate to RS256 or ES256 with asymmetric key pair in KMS. Publish JWKS endpoint. Resource servers validate via public key only. |
| SEC-H07 | **HIGH** | `middleware/auth.py` | `/oauth/introspect` and `/oauth/revoke` are in `PUBLIC_PATHS` — no bearer or client authentication at middleware layer. OpenAPI specifies `clientCredentials` security for introspection, but middleware bypasses it. | Remove OAuth admin endpoints from `PUBLIC_PATHS`. Require client authentication (`private_key_jwt` preferred) before introspection/revocation handlers execute. |
| SEC-H08 | **HIGH** | `middleware/audit.py` | Audit integrity chain has implementation defects: (1) `event["previous_hash"]` is set to post-compute `_last_audit_hash`, same as `integrity_hash`; (2) global mutable state is not safe across concurrent workers; (3) chain does not include request body hash or accessed resource IDs. | Store true `previous_hash` before updating chain head. Use DB serial/sequence for ordering. Include `{method, path, resource_id, request_id, actor}` in hash input. Sign chain segments with HMAC keyed by audit signing key. |
| SEC-H09 | **HIGH** | `core/config.py`, `main.py`, OpenAPI | `RATE_LIMIT_PER_MINUTE=60` is configured and OpenAPI defines `429 TooManyRequests`, but no rate-limiting middleware or gateway rule exists. API is vulnerable to brute-force token attempts and PHI enumeration. | Add Redis-backed sliding window rate limiter (per client_id, IP, and user). Return `Retry-After` header per OpenAPI. Apply stricter limits on auth endpoints. |
| SEC-H10 | **HIGH** | `main.py`, OpenAPI, `README.md` | README claims "TLS 1.2+ enforced via HTTPS redirect middleware" but `HTTPSRedirectMiddleware` is **not registered** in `main.py`. OpenAPI lists `http://localhost:8000` server. No mTLS requirements documented for payer/EHR integrations. | Register `HTTPSRedirectMiddleware` in production. Terminate TLS 1.2+ at load balancer with HSTS. Document and implement mTLS for B2B system scopes (`system/*.read`). Remove plain-HTTP production server entries. |
| SEC-H11 | **HIGH** | OpenAPI `OperationOutcome`, error handlers | `OperationOutcome.issue.diagnostics` and `ProblemDetails.detail` have no sanitization policy. Validation errors on FHIR resources may echo patient identifiers, MRN, or field paths containing PHI. | Implement centralized error sanitizer that strips PHI patterns. Return generic diagnostics to clients; log full details server-side only with access controls. |
| SEC-H12 | **HIGH** | `core/config.py`, `.env.example` | Secrets (`JWT_SECRET_KEY`, `DATABASE_URL` with `changeme` password, `OAUTH2_CLIENT_SECRET`) loaded from flat `.env` files. No production guard prevents placeholder values. No secret rotation automation. | Use managed secrets store with IAM-scoped access. Add startup validator that aborts on placeholder secrets in production. Enable automatic rotation for DB credentials and signing keys. |
| SEC-H13 | **HIGH** | `core/rbac.py` | `Role.ADMIN` has wildcard permission `"*"` granting unrestricted access to all API operations including audit read/write. Over-privileged default role increases blast radius of token compromise. | Apply least privilege: split admin into discrete roles (user admin, config admin). Remove wildcard; enumerate explicit permissions. Require MFA/step-up auth for admin operations. |
| SEC-H14 | **HIGH** | `models/patient.py` | `gender` stored in plaintext. `mrn_token` documented as HMAC of MRN but no HMAC implementation or pepper configuration exists — searchable token scheme is incomplete. | Encrypt or tokenize all PHI fields consistently. Implement HMAC-SHA256 MRN lookup with server-side pepper from secrets manager. |
| SEC-M01 | MEDIUM | `main.py` | CORS configured with `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`. Overly permissive for production cross-origin access to PHI APIs. | Restrict CORS to known frontend origins. Explicitly allow only required headers (`Authorization`, `X-Request-Id`, `Idempotency-Key`). |
| SEC-M02 | MEDIUM | `middleware/request_context.py` | OpenAPI requires `X-Request-Id` (UUID v4) on mutating requests; middleware silently generates one if missing. Client-supplied non-UUID values are accepted without rejection. | Reject mutating requests missing valid `X-Request-Id` per spec. Validate UUID format strictly. |
| SEC-M03 | MEDIUM | `middleware/audit.py` | `X-Audit-Event-Id` response header is emitted even when audit event is not persisted, creating false assurance of audit capture. | Only emit `X-Audit-Event-Id` after durable write confirmation. Return 503 if audit persistence fails (fail-closed for HIPAA). |
| SEC-M04 | MEDIUM | `services/audit_service.py` | `AuditService.log_event()` references non-existent model fields (`actor_id`, `metadata_`, `detail`) — service will fail at runtime if invoked. | Align service with `AuditLog` model schema (`subject_id`, `metadata`, `integrity_hash`, `previous_hash`). |
| SEC-M05 | MEDIUM | OpenAPI | `ClientCredentialsTokenRequest` and `system/*.read` scopes enable broad backend access without documented client registration, certificate binding, or IP allowlisting. | Restrict client_credentials to explicitly registered machine clients with mTLS and minimal scopes. |
| SEC-L01 | LOW | `main.py` | `/health` is unauthenticated (acceptable if non-sensitive). | Ensure health endpoint never exposes version strings, dependency status, or internal topology in production. |
| SEC-L01 | LOW | `core/deps.py` | `HTTPBearer(auto_error=False)` plus manual 401 logic is correct but duplicates validation in `JWTAuthMiddleware`. | Consolidate auth into single middleware or dependency to avoid divergence. |

---

## Overall Risk Rating

| Dimension | Rating | Rationale |
|-----------|--------|-----------|
| **Confidentiality** | CRITICAL | Unencrypted JSONB PHI, ephemeral encryption keys, no patient isolation |
| **Integrity** | CRITICAL | Non-persistent audit logs, broken hash chain, no DB immutability |
| **Availability** | HIGH | No rate limiting; encryption key loss causes permanent data loss |
| **Authentication** | CRITICAL | OAuth stubs, forgeable JWTs, trusted client-side role claims |
| **Authorization** | CRITICAL | Scope/permission bypass vectors; admin wildcard |
| **Audit & Accountability** | CRITICAL | Audit events not durably stored |
| **Transmission Security** | HIGH | TLS not enforced in application layer; no mTLS |

**Composite Overall Risk Rating: CRITICAL**

---

## Immediate Actions Required

Priority-ordered actions that **must** complete before any PHI enters the system:

1. **Block PHI processing** — Deploy only to isolated dev environments with synthetic data until CRITICAL items are closed.
2. **SEC-C02 + SEC-C05** — Integrate KMS for PHI encryption keys; load JWT signing keys from secrets manager; reject placeholder secrets at startup.
3. **SEC-C03 + SEC-C04 + SEC-H05 + SEC-H06** — Implement full OAuth/SMART token lifecycle with server-side role/scope assignment, RS256 + JWKS, refresh rotation, and revocation.
4. **SEC-C01 + SEC-H02 + SEC-H08** — Persist audit logs with DB triggers, correct hash chaining, and fail-closed behavior on write failure.
5. **SEC-H01 + SEC-H14** — Encrypt all PHI at rest including JSONB columns; complete MRN tokenization.
6. **SEC-H03 + SEC-H04 + SEC-H13** — Enforce SMART scopes and patient-context isolation; remove admin wildcard.
7. **SEC-H07** — Authenticate OAuth introspection/revocation endpoints.
8. **SEC-H09 + SEC-H10** — Deploy rate limiting and TLS 1.2+ with HSTS; define mTLS for system integrations.
9. **SEC-H11 + SEC-H12** — Sanitize error responses; migrate all secrets to managed store.
10. **Independent verification** — Penetration test, HIPAA risk assessment, and BAA execution before production go-live.

---

## Positive Security Controls (Phase 1 Intent)

The following design decisions are sound and should be preserved during remediation:

- SMART on FHIR scope taxonomy aligned with ePA use cases in OpenAPI
- PKCE (S256) required in authorization endpoint specification
- AES-256-GCM selected for field-level encryption (correct algorithm)
- Append-only / idempotent API semantics documented for PA and eligibility
- Separate encrypted column design on `PatientRecord` for structured PHI
- Audit correlation headers (`X-Request-Id`, `X-Correlation-Id`, `X-Audit-Event-Id`)
- JWT access token TTL of 15 minutes (appropriate for clinical sessions)
- Production disables `/docs`, `/redoc`, `/openapi.json` exposure
- `TrustedHostMiddleware` enabled in production
- RBAC role separation concept (clinician, billing, payer reviewer, auditor)

---

## Appendix: Files Reviewed

| Path | Purpose |
|------|---------|
| `backend/openapi/epa-platform-v1.yaml` | API contract, OAuth scopes, error schemas |
| `backend/app/core/security.py` | JWT creation/validation |
| `backend/app/core/encryption.py` | PHI field encryption |
| `backend/app/core/rbac.py` | Role and permission definitions |
| `backend/app/core/deps.py` | Auth/RBAC dependency injection |
| `backend/app/core/config.py` | Secrets and security configuration |
| `backend/app/middleware/audit.py` | Audit middleware and hash chain |
| `backend/app/middleware/request_context.py` | Correlation ID propagation |
| `backend/app/middleware/auth.py` | JWT authentication middleware |
| `backend/app/models/*.py` | Data models for PHI, audit, users |
| `backend/app/main.py` | Application middleware stack |
| `backend/app/api/v1/endpoints/oauth.py` | OAuth endpoint stubs |

---

*This report covers Phase 1 scaffold artifacts only. Re-audit required after implementation of remediations and before production deployment.*
