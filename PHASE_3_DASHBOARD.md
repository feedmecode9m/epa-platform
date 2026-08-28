# Phase 3: Secure Provider Dashboard

**Track**: A — Provider Experience (Frontend)  
**Date**: 2026-08-28  
**Data classification**: Synthetic only — not for real PHI

---

## 1. Overview

The Prior Authorization Assistant is a Next.js dashboard that visualizes the Phase 2 backend pipeline:

1. Paste a **synthetic clinical note**
2. View **extracted FHIR criteria** (diagnosis, procedure, conservative therapy duration)
3. See **approval likelihood score** and **documentation gaps**

All API calls proxy through Next.js Route Handlers — the OAuth Bearer token never touches `localStorage` or the browser JavaScript heap.

### Demo screencast (~9 seconds)

[docs/demo/provider-dashboard-demo.webm](docs/demo/provider-dashboard-demo.webm) — also served in the app at `/demo/provider-dashboard-demo.webm`.

```html
<video controls src="docs/demo/provider-dashboard-demo.webm"></video>
```

---

## 2. Architecture

```mermaid
flowchart LR
    Browser[Browser UI] -->|POST /api/analyze| NextAPI[Next.js Route Handlers]
    NextAPI -->|httpOnly cookie| Token[Session Token]
    NextAPI -->|Bearer token server-side| Backend[FastAPI :8000]
    Backend --> NLP[/nlp/extract]
    Backend --> Predict[/prior-authorization/predict]
```

---

## 3. Client-Side Security Measures

| Control | Implementation |
|---------|----------------|
| **Token storage** | httpOnly, `SameSite=Strict`, `Secure` in production — cookie name `epa_session_token` |
| **No localStorage** | Token entered once in password field, sent to `/api/auth/session`, cleared from input |
| **BFF proxy pattern** | Browser never calls FastAPI directly; no CORS token exposure |
| **CSP** | Strict Content-Security-Policy in `next.config.ts` — `connect-src 'self'` only |
| **Clickjacking** | `X-Frame-Options: DENY`, CSP `frame-ancestors 'none'` |
| **MIME sniffing** | `X-Content-Type-Options: nosniff` |
| **PHI logging** | No `console.log` of clinical notes or API responses in client code |
| **XSS** | React auto-escapes rendered note text; no `dangerouslySetInnerHTML` |
| **401/403 handling** | Session cleared on 401; user prompted to reconnect |

### Residual risks (demo environment)

- `'unsafe-inline'` in CSP for Next.js dev — tighten for production build with nonces
- Dev OAuth token pasted manually — production uses full SMART redirect flow
- `Secure` cookie flag disabled in local HTTP dev (enabled automatically in production)

---

## 4. Quick Start

### Terminal 1 — Backend

```bash
cd backend
source venv/bin/activate
docker start epa-postgres   # if not running
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 — Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000**

---

## 5. Acquire a Mock OAuth Token

```bash
# Generate PKCE verifier + challenge
python3 -c "
import hashlib, base64, secrets
v = secrets.token_urlsafe(32)
c = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b'=').decode()
print('VERIFIER:', v)
print('CHALLENGE:', c)
"

# Authorize (open in browser — copy code from redirect URL)
open "http://localhost:8000/oauth/authorize?response_type=code&client_id=epa-smart-client&redirect_uri=http://localhost:3000/callback&scope=launch/patient%20patient/Claim.read%20user/Claim.write%20user/CoverageEligibilityRequest.write&state=xyz&code_challenge=CHALLENGE&code_challenge_method=S256&patient=Patient/synth-patient-0000"

# Exchange code for token
curl -s -X POST http://localhost:8000/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code=CODE_FROM_REDIRECT" \
  -d "redirect_uri=http://localhost:3000/callback" \
  -d "client_id=epa-smart-client" \
  -d "code_verifier=VERIFIER" | jq -r .access_token
```

Paste the token into the dashboard **Connect securely** panel.

---

## 6. End-to-End Demo Flow

1. Connect with OAuth token (httpOnly cookie set)
2. Click **Load sample note** or paste synthetic clinical text
3. Click **Analyze prior authorization**
4. Review:
   - **Extracted FHIR Criteria** — entities with ICD-10/CPT codes, conservative therapy weeks
   - **Approval Likelihood** — score ring, met criteria, documentation gaps

Expected result for the sample spine note: **~85% likelihood**, policy `spine-surgery-lumbar`, gaps for optional documentation items.

---

## 7. File Structure

```
frontend/
├── app/
│   ├── api/
│   │   ├── analyze/route.ts       # BFF: NLP + predict in one call
│   │   └── auth/session/route.ts  # httpOnly cookie management
│   ├── layout.tsx
│   └── page.tsx
├── components/dashboard/
│   ├── AuthPanel.tsx
│   ├── ClinicalNoteInput.tsx
│   ├── Dashboard.tsx
│   ├── ExtractedCriteria.tsx
│   └── PredictionResults.tsx
├── lib/
│   ├── api/server-client.ts       # Server-only backend client
│   ├── auth/session.ts
│   └── types/api.ts
└── next.config.ts                 # CSP + security headers
```

---

## 8. API Routes (Frontend BFF)

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/auth/session` | POST | Store token in httpOnly cookie |
| `/api/auth/session` | DELETE | Clear session |
| `/api/auth/session` | GET | Check connection status |
| `/api/analyze` | POST | Proxy to backend NLP + predict |

---

## 9. Production Checklist (Before Real PHI)

- [ ] Replace manual token paste with SMART on FHIR authorization redirect
- [ ] Enable `Secure` cookies and HTTPS everywhere
- [ ] Tighten CSP (remove `unsafe-eval`, use nonces)
- [ ] Add CSRF tokens for state-changing routes
- [ ] Execute BAAs; integrate production KMS
- [ ] Penetration test frontend + BFF layer

---

*Phase 3 Track A delivers a marketable provider demo while preserving Phase 1.5 security boundaries.*
