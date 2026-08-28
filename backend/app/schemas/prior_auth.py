"""FHIR-aligned prior authorization schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.prior_auth import PriorAuthStatus
from app.schemas.common import FHIRResourceSchema, TimestampedResponse


class PriorAuthRequestCreate(FHIRResourceSchema):
    """FHIR Claim / CDS Hooks prior auth submission."""

    resource_type: str = Field(default="Claim", alias="resourceType")
    patient_id: UUID
    payer_id: UUID | None = None
    external_reference_id: str | None = None
    # FHIR Claim.diagnosis — PHI
    diagnosis_codes: list[str] = Field(
        default_factory=list,
        description="PHI — ICD/SNOMED codes; encrypt before persistence",
    )
    # FHIR Claim.item — PHI clinical service details
    service_details: dict = Field(
        default_factory=dict,
        description="PHI — medication/procedure details; encrypt before persistence",
    )
    clinical_data: dict = Field(
        default_factory=dict,
        description="PHI — supporting clinical documentation; encrypt before persistence",
    )


class PriorAuthRequestResponse(TimestampedResponse):
    id: UUID
    status: PriorAuthStatus
    patient_id: UUID
    requester_id: UUID
    organization_id: UUID
    payer_id: UUID | None = None
    external_reference_id: str | None = None
    status_reason: str | None = None
    payer_response_reference: str | None = None


class PriorAuthStatusQuery(FHIRResourceSchema):
    """Query parameters for prior auth status lookup."""

    request_id: UUID | None = None
    external_reference_id: str | None = None
    patient_id: UUID | None = None


class PriorAuthStatusResponse(FHIRResourceSchema):
    """FHIR ClaimResponse-aligned status response."""

    resource_type: str = Field(default="ClaimResponse", alias="resourceType")
    request_id: UUID
    status: PriorAuthStatus
    status_reason: str | None = None
    payer_response_reference: str | None = None
    last_updated: datetime
    # Non-PHI adjudication summary
    outcome: str | None = None
