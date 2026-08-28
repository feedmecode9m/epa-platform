"""Phase 2 API schemas for NLP extraction and prediction."""

from pydantic import BaseModel, Field


class NLPExtractionRequest(BaseModel):
    clinical_note: str = Field(..., min_length=10, description="Synthetic clinical note text")
    patient_reference: str = Field(default="Patient/synth-patient-0000")
    insurer_reference: str = Field(default="Organization/payer-aetna-synth")


class ExtractedEntityResponse(BaseModel):
    entity_type: str
    text: str
    code: str | None = None
    code_system: str | None = None
    confidence: float


class NLPExtractionResponse(BaseModel):
    entities: list[ExtractedEntityResponse]
    conservative_therapy_weeks: int | None
    coverage_eligibility_request: dict
    confidence_score: float


class PredictionRequest(BaseModel):
    clinical_note: str | None = None
    coverage_eligibility_request: dict | None = None


class DocumentationGap(BaseModel):
    code: str
    description: str
    severity: str


class PredictionResponse(BaseModel):
    approval_likelihood_score: float = Field(ge=0, le=100)
    policy_id: str | None
    policy_name: str | None
    matched_criteria: list[str]
    documentation_gaps: list[DocumentationGap]
    scoring_breakdown: dict[str, float]
    recommendation: str
    coverage_eligibility_request: dict | None = None
