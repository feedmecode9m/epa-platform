# HIPAA Compliance Review — Phase 1

**Reviewer**: `hipaa-compliance` subagent  
**Date**: 2026-08-28  
**Scope**: `backend/openapi/epa-platform-v1.yaml`, `backend/app/` (FastAPI scaffold), `docs/nlp/CLINICAL_NLP_ARCHITECTURE.md`  
**Regulatory Framework**: HIPAA Security Rule (45 CFR §164.308–314), Privacy Rule (§164.502–514)

---

## Executive Summary

Phase 1 artifacts show **strong architectural intent** for a HIPAA-aligned ePA platform: SMART on FHIR OAuth scopes in the OpenAPI spec, RBAC role definitions, AES-256-GCM encryption scaffolding, hash-chained audit design, append-only data model comments, and an NLP architecture that keeps PHI in-memory within a BAA-covered boundary.

**However, the FastAPI scaffold is not production-ready for PHI.** Critical controls exist as placeholders, stubs, or in-memory-only implementations. OAuth is non-functional, audit events are not durably stored, encryption keys are ephemeral, PHI-bearing JSONB columns are written without application-layer encryption, and SMART scope enforcement is absent at the API layer. The NLP module is design-only (not implemented in `backend/app/`).

**Overall Compliance Posture**: **NOT READY** for real PHI. Acceptable as a development scaffold only.

| Verification Area | Design (Spec/Docs) | Implementation (Phase 1 Code) |
|-------------------|--------------------|------------------------------|
| PHI encrypted at rest | ✅ Documented | ❌ Partial — field encryption exists but unused on JSONB; ephemeral key |
| PHI encrypted in transit | ✅ HTTPS servers in OpenAPI | ⚠️ Assumes LB TLS; no app-level TLS/HSTS enforcement |
| RBAC enforced | ✅ Roles + permissions defined | ⚠️ Permission checks on routes; no patient/tenant isolation |
| Immutable audit logging | ✅ OpenAPI + model design | ❌ In-memory only; no DB persistence or triggers |
| Security Rule alignment | ✅ Broad coverage in spec | ❌ Multiple §164.312 controls unimplemented |
| Minimum necessary | ✅ SMART scopes in OpenAPI | ❌ Scopes not enforced; broad JSONB storage |
| BAA considerations | ✅ NLP doc checklist | ❌ No BAAs executed; third-party list incomplete |

---

## Compliant Items (Architectural / Design-Level)

These items are **designed correctly** or partially scaffolded. They do not alone satisfy HIPAA until wired and validated.

| Control | Evidence | HIPAA Reference |
|---------|----------|-----------------|
| **Access control model** | `Role` enum, `ROLE_SCOPE_MAP`, `ROLE_PERMISSIONS`, `require_permission()` in `deps.py`; endpoint guards in `api/v1/endpoints/` | §164.312(a)(1) |
| **Authentication design** | JWT Bearer middleware (`JWTAuthMiddleware`), SMART on FHIR OAuth paths in OpenAPI, PKCE (S256) required in spec | §164.312(d) |
| **Audit control design** | `AuditMiddleware` with hash chaining; `AuditLog` ORM model with `integrity_hash` / `previous_hash`; OpenAPI `X-Audit-Event-Id` headers | §164.312(b) |
| **Integrity control design** | Hash-chained audit events; append-only PA/eligibility semantics in OpenAPI (`Idempotency-Key`, status history) | §164.312(c)(1) |
| **Encryption-at-rest design** | `PHIEncryptionService` (AES-256-GCM); `PatientRecord` encrypted column fields; KMS integration notes | §164.312(a)(2)(iv) |
| **Transmission security (spec)** | Production/staging servers use `https://`; token responses specify `Cache-Control: no-store` | §164.312(e)(1) |
| **Minimum necessary (spec)** | Granular SMART scopes (`patient/Claim.read` vs `user/Claim.write` vs `system/*.read`) | §164.502(b) |
| **NLP PHI handling (doc)** | In-memory processing, no raw note persistence, on-prem model strategy, HITL review gate, Celery payload encryption planned | §164.502(b), §164.312(e) |
| **Immutable resource semantics (spec)** | PA submissions and eligibility checks documented as append-only with correction via linked resources | §164.312(c)(1) |
| **Production hardening hooks** | OpenAPI/docs disabled when `APP_ENV=production`; `TrustedHostMiddleware` in production | §164.308(a)(5) |
| **Correlation / forensics** | `RequestContextMiddleware`, required `X-Request-Id` in OpenAPI, optional `X-Audit-Source` | §164.312(b) |

---

## Gaps and Risks

### CRITICAL

| ID | Risk | Component | Details |
|----|------|-----------|---------|
| **C-01** | **Audit events not persisted** | `middleware/audit.py` | Events are hash-chained in process memory with `# TODO: Persist to append-only audit_log table`. Chain and events are lost on restart. Does not meet §164.312(b) durable audit requirements. |
| **C-02** | **PHI encryption key is ephemeral** | `core/encryption.py` | `PHIEncryptionService` defaults to `os.urandom(32)` per process. `PHI_ENCRYPTION_KEY_ID` is unused. Encrypted data becomes unrecoverable after restart; no KMS envelope encryption or key rotation. |
| **C-03** | **OAuth / SMART authentication is non-functional** | `api/v1/endpoints/oauth.py`, `api/v1/auth.py` | Authorization, token issuance, introspection, and login return placeholders (`501` / static JSON). Deploying as-is would leave PHI endpoints either unreachable or relying on self-issued JWTs without a real IdP. |
| **C-04** | **No Business Associate Agreements executed** | Organization / infra | HIPAA requires BAAs before PHI flows to cloud providers, managed databases, queues, monitoring, terminology servers, or payers. None documented as in place. |
| **C-05** | **Database schema not deployed** | `alembic/versions/0001_initial_placeholder.py` | Migration is a no-op placeholder. Audit immutability triggers are documented in comments only. Tables, RLS, and append-only enforcement do not exist in a runnable state. |
| **C-06** | **Default JWT secret with no startup guard** | `core/config.py`, `core/security.py` | `JWT_SECRET_KEY` defaults to a weak placeholder. No fail-fast check in non-dev environments. Symmetric HS256 signing — acceptable only with proper key management, which is absent. |

### HIGH

| ID | Risk | Component | Details |
|----|------|-----------|---------|
| **H-01** | **FHIR JSONB stores unencrypted PHI** | `models/prior_auth.py`, `services/prior_auth.py` | `claim_resource` JSONB holds full FHIR Claim (names, DOB, diagnoses). `PriorAuthService.submit_request()` persists without `PHIEncryptionService`. Same risk for `PatientRecord.fhir_resource`. |
| **H-02** | **No database-level audit immutability** | `models/audit_log.py`, Alembic | Comments reference append-only triggers; no migration creates `BEFORE UPDATE OR DELETE` triggers or revoked privileges. Application-layer guards alone are insufficient. |
| **H-03** | **SMART scopes not enforced on API routes** | `core/deps.py`, endpoints | `require_scope()` exists but is **never used**. Endpoints use role permissions only, not OpenAPI-declared SMART scopes. Breaks minimum-necessary alignment between spec and runtime. |
| **H-04** | **No patient / tenant access isolation** | `services/prior_auth.py`, endpoints | `get_status()` returns placeholder data without verifying the caller's `patient` context or organization. Any authenticated user with `prior_auth:read` could access any record once DB lookup is implemented. |
| **H-05** | **Transmission security not enforced in application** | `main.py`, README | README claims "HTTPS redirect middleware"; **not implemented**. OpenAPI lists `http://localhost:8000`. Production relies entirely on external TLS termination with no HSTS, no redirect, no mTLS for internal services. |
| **H-06** | **Audit log incomplete for HIPAA forensics** | `middleware/audit.py` | Events omit `resource_type`, `resource_id`, and SMART client attribution. `previous_hash` is incorrectly set equal to `integrity_hash` (line 59). `AuditService` references non-existent model fields (`actor_id`, `metadata_`, `detail`) — service is non-functional. |
| **H-07** | **Automatic logoff / session controls incomplete** | Auth layer | 15-minute JWT expiry is configured, but refresh token rotation, revocation enforcement, and idle timeout are not implemented. OpenAPI describes refresh/revoke endpoints; stubs only. §164.312(a)(2)(iii) gap. |
| **H-08** | **Error responses may leak PHI or internals** | OpenAPI `OperationOutcome.diagnostics` | Spec allows diagnostic strings in FHIR errors. No server-side sanitization layer exists. Validation failures on FHIR Bundles could echo patient identifiers. |
| **H-09** | **No contingency / backup / DR architecture** | Infrastructure | §164.308(a)(7) requires backup, disaster recovery, and emergency mode operations. Not documented or implemented for PostgreSQL, audit logs, or encryption keys. |
| **H-10** | **NLP pipeline not implemented; queue security unspecified** | `CLINICAL_NLP_ARCHITECTURE.md` | Celery + Redis planned for PHI job delivery. Encrypted payloads and mTLS are documented as goals but not present in code. Redis without TLS/encryption would expose PHI in transit between API and workers. |
| **H-11** | **No rate limiting on PHI endpoints** | `config.py`, middleware | `RATE_LIMIT_PER_MINUTE=60` configured but no middleware. OpenAPI defines `429 TooManyRequests` — not enforced. Increases brute-force and data-exfiltration risk. |
| **H-12** | **External LLM PHI exfiltration risk (future)** | NLP architecture Phase 4 | Architecture correctly recommends on-prem models, but no code-level guard prevents future integration with non-BAA LLM APIs. Policy-only control. |

### MEDIUM

| ID | Risk | Component | Details |
|----|------|-----------|---------|
| **M-01** | CORS defaults include `http://localhost:3000` | `core/config.py` | Acceptable for dev; must be locked to production origins. |
| **M-02** | No HIPAA consent / authorization tracking | Data model | No `Consent` FHIR resource or authorization record for uses/disclosures beyond TPO. |
| **M-03** | OpenAPI audit headers not validated | Middleware / endpoints | Spec requires `X-Request-Id`, `Idempotency-Key`; middleware generates IDs if missing rather than rejecting non-compliant clients. |
| **M-04** | Duplicate / stale route modules | `api/v1/prior_authorization.py` vs `endpoints/` | Parallel scaffold files increase risk of deploying wrong RBAC or missing guards. |
| **M-05** | Database credentials in default config | `core/config.py`, `.env.example` | `changeme` default password — must use secrets manager and least-privilege DB roles. |
| **M-06** | NLP auto-approve threshold | NLP doc §8.2 | Auto-approve at ≥0.90 confidence could bypass HITL for clinically significant errors; needs conservative platform default. |

### LOW

| ID | Risk | Component | Details |
|----|------|-----------|---------|
| **L-01** | Health endpoint unauthenticated | `main.py` | Acceptable if response contains no sensitive metadata. |
| **L-02** | `.env.example` placeholder secrets | Config | Expected for scaffold; enforce vault in CI/CD. |
| **L-03** | AI prediction placeholder in PA status | `services/prior_auth.py` | Returns hardcoded scores; ensure model inference does not log PHI when implemented. |

---

## Verification Details

### 1. PHI Encrypted at Rest and in Transit

**At rest — FAIL (partial design)**  
- `PHIEncryptionService` implements AES-256-GCM but uses a random per-process key.  
- `PatientRecord` defines encrypted columns; `PriorAuthorization.claim_resource` does not use encryption.  
- README references PostgreSQL TDE; not configured in migrations or infra docs.

**In transit — PARTIAL**  
- OpenAPI production servers use HTTPS.  
- No `HTTPSRedirectMiddleware`, HSTS headers, or certificate pinning in `main.py`.  
- NLP doc specifies TLS 1.2+ and encrypted Celery payloads — not implemented.

### 2. RBAC Enforced

**PARTIAL**  
- Routes use `require_permission("prior_auth:create")` etc.  
- Gaps: no SMART scope checks, no patient-context binding, no multi-tenant RLS, admin role has `"*"` wildcard.

### 3. Immutable Audit Logging in Middleware

**FAIL (design only)**  
- Middleware computes hash chain and sets `X-Audit-Event-Id`.  
- Events are not written to PostgreSQL.  
- DB triggers for append-only enforcement are commented, not migrated.

### 4. HIPAA Security Rule Alignment

| Safeguard | Status | Notes |
|-----------|--------|-------|
| §164.312(a)(1) Access control | ⚠️ | RBAC scaffold; no unique user tracking in audit persistence |
| §164.312(a)(2)(iii) Automatic logoff | ⚠️ | JWT expiry only |
| §164.312(a)(2)(iv) Encryption | ❌ | Ephemeral keys; JSONB gap |
| §164.312(b) Audit controls | ❌ | Not persisted |
| §164.312(c)(1) Integrity | ⚠️ | Hash chain in memory; no WORM storage |
| §164.312(d) Person/entity authentication | ❌ | OAuth stubs |
| §164.312(e)(1) Transmission security | ⚠️ | Spec-level HTTPS; app enforcement missing |
| §164.308(a)(7) Contingency plan | ❌ | Not architected |

### 5. Minimum Necessary Principle

**FAIL at implementation layer**  
- OpenAPI scopes are granular and appropriate.  
- Backend enforces coarse role permissions, not scopes.  
- Full FHIR resources stored/returned without field-level access filtering.  
- NLP doc aligns with minimum necessary (PA-relevant entities only, no note retention) — design-only.

### 6. BAA Considerations for Third-Party Services

See BAA Checklist below. NLP architecture correctly flags third-party LLM APIs as requiring BAA or prohibition. No vendor agreements or subprocessors register exists in the repo.

---

## Remediation Recommendations

### Immediate — Block PHI Processing

1. **Persist audit logs**: Wire `AuditMiddleware` to `AuditService` → `audit_logs` table; fix model field mismatches; implement Alembic migration with append-only triggers.
2. **KMS-backed encryption**: Replace `os.urandom(32)` with envelope encryption (AWS KMS / Azure Key Vault / GCP Cloud KMS); encrypt all JSONB PHI columns.
3. **Complete OAuth 2.0 / SMART**: Implement authorization code + PKCE, token issuance (RS256 + JWKS), introspection, and revocation per OpenAPI spec.
4. **Startup security guard**: Refuse boot in staging/production if default secrets detected.
5. **Execute BAAs**: Cloud provider, managed PostgreSQL, Redis, monitoring, payer connectivity, EHR partners — before any PHI.

### Short-Term — Pre-Production

6. Enforce SMART scopes via `require_scope()` on every PHI endpoint; bind patient-context tokens to resource queries.  
7. Add PostgreSQL RLS for multi-tenant patient isolation.  
8. Implement `HTTPSRedirectMiddleware` + HSTS in production; mTLS for internal Celery/Redis when NLP is built.  
9. Sanitize all client-facing errors; log diagnostics server-side only.  
10. Add Redis-backed rate limiting on auth and PHI routes.  
11. Deploy real Alembic schema from ORM models.

### Before Production Go-Live

12. Document and test backup/DR (RPO/RTO targets, encrypted backups, key recovery).  
13. Complete HIPAA risk assessment and workforce training documentation.  
14. Penetration test and vulnerability scan.  
15. Implement NLP with on-prem models only (v1); code-level block on external LLM API calls without BAA flag.  
16. Add `Consent` tracking where required by Privacy Rule.

---

## BAA Checklist

| Vendor / Service | PHI Exposure | BAA Required | Phase 1 Status | Action |
|------------------|-------------|--------------|----------------|--------|
| **Cloud provider** (AWS / Azure / GCP) | Hosting, KMS, object storage | Yes | ❌ Not executed | Sign BAA before deploy; enable HIPAA-eligible services only |
| **Managed PostgreSQL** (RDS, Cloud SQL, etc.) | All structured PHI | Yes | ❌ Not executed | Use HIPAA tier; enable encryption at rest + automated backups |
| **Redis** (Celery broker / NLP cache) | Job payloads may contain PHI | Yes | ❌ Not executed | Enable TLS in transit; encryption at rest; VPC isolation |
| **Celery workers** (NLP GPU pool) | In-memory PHI during extraction | Covered under cloud BAA | ⚠️ Not built | Deploy inside same BAA-covered VPC; no persistent disks |
| **Monitoring / APM** (Datadog, New Relic, Sentry) | Logs must exclude PHI | Yes | ❌ Not executed | Configure PHI scrubbing; sign BAA or use self-hosted |
| **External LLM APIs** (OpenAI, Anthropic, etc.) | Raw clinical notes | Yes — or **prohibit** | ⚠️ Policy in NLP doc only | Block at network/code level; use on-prem models in v1 |
| **Terminology server** (Ontoserver / NLMTS) | Code lookups (low PHI) | Depends on query content | ❌ Not evaluated | Self-host or BAA; avoid patient identifiers in queries |
| **EHR / FHIR integration partner** | Full PHI exchange | Yes | ❌ Not executed | BAA + SMART app registration per tenant |
| **Payer / clearinghouse** | PA and eligibility PHI | Yes | ❌ Not executed | Standard trading partner agreements |
| **Identity provider** (Auth0, Okta, Azure AD) | User identity, possibly ePHI in claims | Yes | ❌ Not configured | Enable HIPAA BAA tier; minimize claims to roles/scopes |
| **Email / SMS notifications** | Potential PHI in message body | Yes | ❌ Not applicable yet | Use vendor with BAA; never include PHI in notifications |
| **CDN / WAF** (Cloudflare, etc.) | TLS-terminated traffic | Yes if PHI in headers/body | ❌ Not evaluated | Enterprise BAA or terminate TLS at HIPAA-eligible LB |

---

## Conclusion

Phase 1 correctly **anticipates** HIPAA Technical Safeguards in specification and scaffold structure. It does **not** yet **implement** them at a level safe for ePHI. **Do not process real patient data** until all CRITICAL items (C-01 through C-06) are resolved and HIGH items affecting encryption, access control, audit durability, and transmission security are remediated.

---

*Document version: 1.1 · Review type: Phase 1 artifact assessment · Next review: After OAuth, audit persistence, and KMS encryption are implemented*
