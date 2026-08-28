"""FHIR-aligned Pydantic schema placeholders."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FHIRResourceBase(BaseModel):
    resourceType: str
    id: str | None = None
    meta: dict[str, Any] | None = None


class ClaimResource(FHIRResourceBase):
    resourceType: str = "Claim"
    status: str = "active"
    type: dict[str, Any] | None = None
    use: str = "preauthorization"
    patient: dict[str, Any] | None = None
    insurer: dict[str, Any] | None = None
    item: list[dict[str, Any]] = Field(default_factory=list)


class ClaimResponseResource(FHIRResourceBase):
    resourceType: str = "ClaimResponse"
    status: str = "active"
    outcome: str | None = None
    disposition: str | None = None
    preAuthRef: str | None = None


class CoverageEligibilityRequestResource(FHIRResourceBase):
    resourceType: str = "CoverageEligibilityRequest"
    status: str = "active"
    purpose: list[str] = Field(default_factory=lambda: ["benefits"])
    patient: dict[str, Any]
    insurer: dict[str, Any]
    created: datetime
    item: list[dict[str, Any]] = Field(default_factory=list)


class CoverageEligibilityResponseResource(FHIRResourceBase):
    resourceType: str = "CoverageEligibilityResponse"
    status: str = "active"
    outcome: str | None = None
    patient: dict[str, Any] | None = None
    insurer: dict[str, Any] | None = None
    insurance: list[dict[str, Any]] = Field(default_factory=list)


class PriorAuthRequestBundle(BaseModel):
    resourceType: str = "Bundle"
    type: str = "collection"
    entry: list[dict[str, Any]]


class PriorAuthStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    APPROVED = "approved"
    DENIED = "denied"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class ApprovalLikelihood(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
    factors: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class PriorAuthStatusResponse(BaseModel):
    tracking_id: UUID
    status: PriorAuthStatus
    patient_id: str | None = None
    claim_response: ClaimResponseResource | None = None
    ai_prediction: ApprovalLikelihood | None = None
    last_updated: datetime
    audit_trail_ref: UUID | None = None


class OperationOutcomeIssue(BaseModel):
    severity: str
    code: str
    diagnostics: str | None = None


class OperationOutcome(BaseModel):
    resourceType: str = "OperationOutcome"
    issue: list[OperationOutcomeIssue]
