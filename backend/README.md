# EPA Platform Backend

HIPAA-compliant electronic Prior Authorization (ePA) platform API built with FastAPI, SQLAlchemy 2.0 (async), and PostgreSQL.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (recommended for production HIPAA workloads)

## Quick Start

```bash
cd backend

python -m venv venv
source venv/bin/activate

pip install -e ".[dev]"

cp .env.example .env
# Edit .env — set JWT_SECRET_KEY to a secure random value

alembic upgrade head   # after PostgreSQL is available

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## Directory Structure

```
backend/
├── alembic/                      # Database migrations
│   └── versions/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/            # Route handlers
│   │   │   ├── prior_authorization.py
│   │   │   ├── eligibility.py
│   │   │   └── oauth.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   ├── deps.py               # Dependency injection
│   │   ├── encryption.py         # PHI field-level encryption
│   │   ├── rbac.py               # Role-based access control
│   │   └── security.py           # JWT + OAuth token utilities
│   ├── middleware/
│   │   ├── auth.py               # JWT authentication middleware
│   │   ├── audit.py              # Immutable audit logging middleware
│   │   └── request_context.py    # Correlation / request ID propagation
│   ├── models/
│   │   ├── audit_log.py          # Append-only audit trail
│   │   ├── patient.py            # PHI fields encrypted at rest
│   │   ├── prior_auth.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── fhir.py               # FHIR-aligned Pydantic placeholders
│   │   ├── patient.py
│   │   └── prior_auth.py
│   ├── services/
│   │   ├── prior_auth.py
│   │   ├── eligibility.py
│   │   ├── audit_service.py
│   │   └── encryption_service.py
│   └── main.py
├── openapi/                      # OpenAPI + FHIR profile references
├── pyproject.toml
├── alembic.ini
└── .env.example
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/prior-authorization/request` | Submit prior auth request |
| GET | `/api/v1/prior-authorization/status/{tracking_id}` | Get prior auth status |
| POST | `/api/v1/patient/eligibility` | Check patient eligibility |
| GET | `/.well-known/smart-configuration` | SMART on FHIR discovery |
| POST | `/oauth/token` | OAuth2 token endpoint (placeholder) |

## Security Architecture

### JWT Authentication

- Tokens created via `create_access_token()` in `app/core/security.py`
- Validated in `JWTAuthMiddleware` and `get_current_user` dependency
- Public paths: `/health`, `/docs`, SMART/OAuth discovery endpoints

### OAuth2 / OIDC Integration

Set `OAUTH2_ENABLED=true` and configure IdP variables in `.env`. Implement JWKS validation in `validate_oauth2_token()` (`app/core/security.py`).

SMART on FHIR endpoints in `app/api/v1/endpoints/oauth.py` provide discovery and token exchange placeholders.

### RBAC

- Roles and permissions: `app/core/rbac.py`
- SMART scope mapping for FHIR-aligned authorization
- Enforce via `require_permission()` / `require_scope()` in `app/core/deps.py`

### PHI Encryption at Rest

- `PHIEncryptionService` in `app/core/encryption.py` (AES-256-GCM placeholder)
- All PHI model columns prefixed/suffixed with `encrypted_` — encrypt before DB write
- Production: envelope encryption via AWS KMS / Azure Key Vault / GCP Cloud KMS

### Immutable Audit Logging

- `AuditMiddleware` hash-chains request events
- `AuditLog` model is append-only — enforce with PostgreSQL triggers (see migration placeholder)
- Never store PHI in audit metadata — resource IDs only

## Development

```bash
ruff check app
pytest
alembic revision --autogenerate -m "describe change"
```

Generate secrets:

```bash
openssl rand -hex 32
```
