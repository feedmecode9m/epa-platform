# Design Partner Outreach — Email Template

**Audience:** Health IT Director, VP of Revenue Cycle Management, or Compliance / Privacy Officer at a mid-sized regional health plan or independent specialty provider network.

**Tone:** Formal, risk-aware, concise. Lead with compliance and operational risk—not hype.

---

## Subject line options

1. `CMS-0057-F and prior auth: a security-first ePA demo (9-second walkthrough)`
2. `Reducing PA rework with documentation-gap scoring — design partner inquiry`
3. `Immutable audit trail for ePA workflows — brief intro for [Organization]`

---

## Body template

```text
Dear [Name],

I am writing to introduce a security-first electronic Prior Authorization (ePA) platform I have built for organizations under increasing CMS interoperability pressure and continuing administrative burden from incomplete PA submissions.

Most solutions lead with automation. This platform leads with forensic controls: an HMAC-signed, hash-chained audit trail; Backend-for-Frontend session handling (no tokens in localStorage); SMART on FHIR / OAuth2 with PKCE; and a synthetic-data posture that does not process real PHI until Business Associate Agreements and production key management are in place.

Functionally, the Provider Assistant:
• Extracts structured FHIR criteria from clinical notes
• Scores approval likelihood against payer policy rules
• Surfaces documentation gaps before submission

A nine-second product walkthrough is available here:
[Link to docs/demo/provider-dashboard-demo.webm or hosted demo URL]

I am seeking one design partnership with a mid-sized regional plan or specialty network to validate workflow fit, refine payer rulebooks, and align SMART on FHIR launch requirements to your EHR environment.

Would you be open to a 20-minute technical walkthrough in the next two weeks? I can also share a one-page technical brief in advance.

Respectfully,
[Full Name]
[Title / Background — e.g., Founder; Digital Forensics & Data Security]
[Email] | [Phone] | [LinkedIn or GitHub]
```

---

## Optional short follow-up (Day 5–7)

```text
Subject: Re: CMS-0057-F and prior auth — design partner inquiry

Dear [Name],

Brief follow-up on my note regarding a security-first ePA assistant (FHIR extraction, approval-likelihood scoring, and forensic audit logging). Happy to send the one-pager and 9-second walkthrough asynchronously if a live call is difficult this month.

Best regards,
[Name]
```

---

## Personalization checklist

- [ ] Replace `[Name]` / `[Organization]` with researched titles
- [ ] Mention one specific PA pain point for their specialty (e.g., spine, oncology, rheumatology)
- [ ] Attach or link [`ONE_PAGER.md`](ONE_PAGER.md) as PDF when exporting
- [ ] Host or attach `provider-dashboard-demo.webm` (GitHub raw / Loom / private Drive)
- [ ] Do **not** claim HIPAA certification, BAAs signed, or live PHI production readiness

---

## What not to say

| Avoid | Prefer |
|-------|--------|
| “HIPAA certified” / “fully compliant” | “HIPAA-aware architecture; synthetic-only until BAAs + KMS” |
| “Replaces your EHR” | “Assists PA workflow; SMART on FHIR launch on roadmap” |
| Guaranteed approval rates | “Likelihood scoring and gap detection to reduce incomplete submissions” |
