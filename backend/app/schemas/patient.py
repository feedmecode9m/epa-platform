"""FHIR-aligned Patient and eligibility schemas."""

from datetime import date
from uuid import UUID

from pydantic import Field

from app.schemas.common import (
    Address,
    AdministrativeGender,
    FHIRResourceSchema,
    HumanName,
    Identifier,
    TimestampedResponse,
)


class PatientCreate(FHIRResourceSchema):
    """FHIR Patient resource — create request."""

    resource_type: str = Field(default="Patient", alias="resourceType")
    identifier: list[Identifier] = Field(default_factory=list)
    name: list[HumanName] = Field(default_factory=list)
    birth_date: date | None = Field(None, alias="birthDate", description="PHI")
    gender: AdministrativeGender | None = None
    address: list[Address] = Field(default_factory=list)
    organization_id: UUID


class PatientResponse(TimestampedResponse):
    """Patient response — PHI fields returned decrypted by service layer only."""

    resource_type: str = Field(default="Patient", alias="resourceType")
    member_id: str = Field(..., description="PHI — decrypted at read time")
    given_name: str = Field(..., description="PHI")
    family_name: str = Field(..., description="PHI")
    birth_date: date = Field(..., description="PHI")
    gender: AdministrativeGender | None = None
    organization_id: UUID


class CoverageEligibilityRequest(FHIRResourceSchema):
    """FHIR CoverageEligibilityRequest — eligibility check input."""

    resource_type: str = Field(default="CoverageEligibilityRequest", alias="resourceType")
    patient_id: UUID | None = None
    member_id: str | None = Field(None, description="PHI — member/subscriber ID")
    payer_id: UUID | None = None
    service_type: str | None = Field(None, alias="serviceType")
    # FHIR item — procedure/medication codes
    item: list[dict] = Field(default_factory=list)


class CoverageEligibilityResponse(FHIRResourceSchema):
    """FHIR CoverageEligibilityResponse — eligibility check result."""

    resource_type: str = Field(default="CoverageEligibilityResponse", alias="resourceType")
    patient_id: UUID | None = None
    eligible: bool
    coverage_status: str = Field(..., alias="coverageStatus")
    prior_auth_required: bool = Field(default=False, alias="priorAuthRequired")
    details: list[dict] = Field(default_factory=list)
    disposition: str | None = None
