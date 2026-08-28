"""Clinical NLP extraction endpoints."""

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, require_scope_and_permission
from app.schemas.phase2 import (
    ExtractedEntityResponse,
    NLPExtractionRequest,
    NLPExtractionResponse,
)
from app.services.nlp_extractor import ClinicalNLPExtractor

router = APIRouter()
_extractor = ClinicalNLPExtractor()


@router.post("/extract", response_model=NLPExtractionResponse, summary="Extract FHIR criteria from clinical note")
async def extract_clinical_note(
    request: NLPExtractionRequest,
    user: CurrentUser = Depends(
        require_scope_and_permission("user/CoverageEligibilityRequest.write", "eligibility:check")
    ),
):
    result = _extractor.extract(
        request.clinical_note,
        request.patient_reference,
        request.insurer_reference,
    )
    return NLPExtractionResponse(
        entities=[
            ExtractedEntityResponse(
                entity_type=e.entity_type,
                text=e.text,
                code=e.code,
                code_system=e.code_system,
                confidence=e.confidence,
            )
            for e in result.entities
        ],
        conservative_therapy_weeks=result.conservative_therapy_weeks,
        coverage_eligibility_request=result.coverage_eligibility_request or {},
        confidence_score=result.confidence_score,
    )
