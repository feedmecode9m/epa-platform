# FHIR Resource Mappings — EPA Platform v1

This document maps EPA Platform REST endpoints to HL7 FHIR R4 resources and
implementation guide profiles.

## Endpoint → FHIR Resource Map

| Platform Endpoint | HTTP | Primary FHIR Resources | IG Profile |
|---|---|---|---|
| `/api/v1/prior-authorization/request` | POST | `Claim`, `Patient`, `Coverage`, `PractitionerRole`, `Organization` | [Da Vinci PAS Claim](http://hl7.org/fhir/us/davinci-pas/StructureDefinition/davinci-pas-claim) |
| `/api/v1/prior-authorization/status/{id}` | GET | `ClaimResponse`, `Task`, `Claim` (reference) | [Da Vinci PAS ClaimResponse](http://hl7.org/fhir/us/davinci-pas/StructureDefinition/davinci-pas-claimresponse) |
| `/api/v1/patient/eligibility` | POST | `CoverageEligibilityRequest` → `CoverageEligibilityResponse` | [US Drug Formulary CER](http://hl7.org/fhir/us/davinci-drug-formulary/StructureDefinition/usdf-coverageeligibilityrequest) |

## Cross-Cutting Resources

| Resource | Role |
|---|---|
| `AuditEvent` | Server-generated immutable audit record for every API operation (HIPAA §164.312(b)) |
| `OperationOutcome` | Validation errors and business-rule failures |
| `Bundle` (type=`collection`) | Composite submission wrapper for multi-resource PA/eligibility payloads |
| `Task` | Workflow state machine for PA lifecycle tracking |
| `Communication` | *(future)* Payer–provider messaging for additional info requests |

## Prior Authorization (`Claim`)

- **`Claim.use`**: Must be `preauthorization`
- **`Claim.status`**: Submissions use `active`; cancellations create a new related Claim with `status: cancelled`
- **`Claim.related`**: Links amendments; original submissions are never mutated
- **`Claim.item`**: Service lines (medication, procedure, DME) with RxNorm/HCPCS/CPT coding
- **`Claim.supportingInfo`**: Clinical attachments referenced by valueAttachment or DocumentReference

## Eligibility (`CoverageEligibilityRequest`)

- **`purpose`**: At least one of `auth-requirements`, `benefits`, `discovery`, `validation`
- **`insurance.coverage`**: Reference to active `Coverage` resource
- **Response `insurance.inforce`**: Boolean coverage active indicator
- **Response `insurance.item.benefit`**: Benefit details including auth-required flags

## Audit & Immutability Extensions

Platform-specific `Meta.extension` URLs (to be registered):

| Extension URL | Value | Purpose |
|---|---|---|
| `https://epa-platform.example.com/fhir/StructureDefinition/audit-chain-sequence` | integer | Monotonic audit log index |
| `https://epa-platform.example.com/fhir/StructureDefinition/audit-chain-hash` | string (SHA-256) | Tamper-evident chain link |
| `https://epa-platform.example.com/fhir/StructureDefinition/idempotency-key` | string (UUID) | Client deduplication key |
| `https://epa-platform.example.com/fhir/StructureDefinition/platform-request-id` | string | Platform-assigned PA request ID |

## SMART on FHIR Scope → Resource Access

| Scope | Permitted Operations |
|---|---|
| `patient/Patient.read` | Read Patient in patient context |
| `patient/Coverage.read` | Read Coverage for contextual patient |
| `patient/Claim.read` | Read PA status for contextual patient |
| `patient/Claim.write` | Submit PA for contextual patient |
| `patient/CoverageEligibilityRequest.write` | Submit eligibility check for contextual patient |
| `user/Claim.write` | Submit PA for any accessible patient |
| `user/CoverageEligibilityRequest.write` | Submit eligibility for any accessible patient |
| `user/CoverageEligibilityResponse.read` | Read eligibility results |
| `system/AuditEvent.read` | Audit service access to immutable logs |

## Terminology Bindings

| Element | ValueSet / CodeSystem |
|---|---|
| `Claim.type` | [Claim Type](http://hl7.org/fhir/ValueSet/claim-type) |
| `Claim.item.productOrService` | RxNorm, CPT, HCPCS per line type |
| `ClaimResponse.outcome` | [Claim Processing Codes](http://hl7.org/fhir/ValueSet/remittance-outcome) |
| `CoverageEligibilityRequest.purpose` | [Eligibility Request Purpose](http://hl7.org/fhir/ValueSet/eligibilityrequest-purpose) |
| `Task.status` | [Task Status](http://hl7.org/fhir/ValueSet/task-status) |

## Validation

Production validation SHOULD enforce StructureDefinition profiles via FHIR
validator (e.g., `$validate` operation or server-side HAPI FHIR validation).
The OpenAPI schemas in `epa-platform-v1.yaml` represent a structural subset;
full conformance requires IG profile validation.
