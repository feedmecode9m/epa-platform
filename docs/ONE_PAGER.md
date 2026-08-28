# ePA Platform — Technical One-Pager

**Electronic Prior Authorization · Security-First · FHIR R4 · Synthetic MVP Ready for Design Partners**

---

## The Problem

Prior authorization remains one of the most expensive friction points in U.S. care delivery:

- **Administrative burden** — Clinicians and revenue-cycle teams spend hours chasing incomplete submissions, denials, and rework.
- **Regulatory pressure** — CMS-0057-F and related interoperability rules push payers and providers toward electronic, standards-based PA workflows (FHIR, SMART on FHIR), with little room for fragile one-off portals.
- **Audit and risk exposure** — Every PHI access and PA decision must be explainable under HIPAA. Most point solutions treat audit logs as afterthoughts—not forensic evidence.

Regional health plans and independent specialty networks face this gap acutely: they need CMS-aligned ePA capability without enterprise EHR lock-in or security theater.

---

## The Solution

**ePA Platform** is an AI-assisted electronic Prior Authorization assistant that:

1. Accepts a clinical note (synthetic today; PHI only after BAAs + production KMS).
2. Extracts structured FHIR criteria (diagnosis, procedure, conservative treatment duration).
3. Scores **approval likelihood** against a mock payer policy rulebook.
4. Surfaces **documentation gaps** before submission—so incomplete packets never leave the desk.

| Capability | What partners see |
|------------|-------------------|
| Clinical NLP (local, rule-based) | Note → FHIR `CoverageEligibilityRequest` fields |
| Predictive rules engine | Likelihood score (0–100%) + gap checklist |
| Provider dashboard | Next.js UI with live walkthrough video |
| SMART on FHIR / OAuth2 + PKCE | Auth foundation for EHR launch (Track B roadmap) |

**Product walkthrough:** [GIF on GitHub](https://github.com/feedmecode9m/epa-platform#product-walkthrough--13-seconds) · [MP4 download](https://github.com/feedmecode9m/epa-platform/releases/download/demo-v1/provider-dashboard-demo.mp4)

---

## The Differentiator: Security & Forensic Auditability

Most health-tech demos lead with “AI.” We lead with **chain of custody**.

| Control | Why it matters to a Health IT / Compliance buyer |
|---------|--------------------------------------------------|
| **HMAC-signed, hash-chained audit log** | Tamper-evident trail for every PHI-adjacent API access (HIPAA §164.312(b) design) |
| **Backend-for-Frontend (BFF)** | Browser never holds Bearer tokens in `localStorage`; server-side proxy only |
| **httpOnly session cookies** | Mitigates XSS-based token theft |
| **Strict CSP + security headers** | Clickjacking / injection surface reduced by default |
| **JWKS / RS256 + server-side scope grants** | Roles and SMART scopes are **not** trusted from client-declared JWT claims |
| **Envelope encryption scaffolding (mock KMS)** | Path to production KMS without rewriting the data model |
| **Synthetic-first posture** | No real PHI until BAAs and production key management are in place |

**Founder context:** Built by an engineer with a background in **digital forensics and data security**—the audit trail is designed for evidentiary integrity, not checkbox logging.

---

## Current Status (Honest)

| Ready now | Not yet (by design) |
|-----------|---------------------|
| Local full-stack demo (synthetic) | Production AWS/Azure KMS |
| Security-hardened Phase 1.5 backend | Signed BAAs / live PHI |
| Provider dashboard + embedded screencast | Live Epic / HAPI EHR launch (planned Track B) |
| Design-partner evaluation | One-click HIPAA cloud deploy |

---

## Design Partnership Ask

We are seeking **1–2 mid-sized regional health plans or independent specialty provider networks** to:

1. Validate workflow fit with real (sandbox or de-identified) PA scenarios.
2. Prioritize payer rulebook and documentation-gap taxonomies.
3. Co-define SMART on FHIR launch requirements for their EHR footprint.

**Contact:** [Your name / email] · Request a 20-minute walkthrough.

*Synthetic data only until BAAs and production encryption are executed.*
