"""Shared FHIR-aligned schema primitives."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FHIRResourceSchema(BaseModel):
    """Base schema for FHIR-aligned resources."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HumanName(FHIRResourceSchema):
    """FHIR HumanName datatype subset."""

    use: str | None = None
    family: str | None = Field(None, description="PHI — encrypt before persistence")
    given: list[str] = Field(default_factory=list, description="PHI — encrypt before persistence")


class Identifier(FHIRResourceSchema):
    """FHIR Identifier datatype."""

    system: str | None = None
    value: str = Field(..., description="PHI — encrypt before persistence")


class Address(FHIRResourceSchema):
    """FHIR Address datatype subset."""

    line: list[str] = Field(default_factory=list, description="PHI — encrypt before persistence")
    city: str | None = Field(None, description="PHI — encrypt before persistence")
    state: str | None = None
    postal_code: str | None = Field(None, alias="postalCode", description="PHI")
    country: str | None = "US"


class AdministrativeGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class OperationOutcome(FHIRResourceSchema):
    """FHIR OperationOutcome for error responses."""

    resource_type: str = Field(default="OperationOutcome", alias="resourceType")
    issue: list[dict] = Field(default_factory=list)


class PaginatedResponse(FHIRResourceSchema):
    total: int
    offset: int = 0
    limit: int = 50
    items: list


class TimestampedResponse(FHIRResourceSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
