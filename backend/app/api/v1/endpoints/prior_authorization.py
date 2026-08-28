"""Prior authorization endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbSession, require_scope_and_permission
from app.schemas.phase2 import (
    DocumentationGap,
    NLPExtractionRequest,
    PredictionRequest,
    PredictionResponse,
)
from app.schemas.fhir import (
    PriorAuthRequestBundle,
    PriorAuthStatusResponse,
)
from app.services.nlp_extractor import ClinicalNLPExtractor
from app.services.prediction_engine import PredictiveRulesEngine
from app.services.prior_auth import PriorAuthService

router = APIRouter()
_nlp = ClinicalNLPExtractor()
_predictor = PredictiveRulesEngine()


@router.post(
    "/request",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    summary="Submit prior authorization request",
)
async def create_prior_authorization(
    bundle: PriorAuthRequestBundle,
    db: DbSession,
    user: CurrentUser = Depends(require_scope_and_permission("user/Claim.write", "prior_auth:create")),
):
    service = PriorAuthService(db)
    result = await service.submit_request(bundle, submitted_by=user.id)
    return result


@router.get(
    "/status/{tracking_id}",
    response_model=PriorAuthStatusResponse,
    summary="Get prior authorization status",
)
async def get_prior_authorization_status(
    tracking_id: UUID,
    db: DbSession,
    user: CurrentUser = Depends(require_scope_and_permission("patient/Claim.read", "prior_auth:read")),
):
    service = PriorAuthService(db)
    status_response = await service.get_status(tracking_id)
    if status_response.patient_id:
        user.assert_patient_access(status_response.patient_id)
    return status_response


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict prior authorization approval likelihood",
)
async def predict_prior_authorization(
    request: PredictionRequest,
    user: CurrentUser = Depends(require_scope_and_permission("user/Claim.write", "prior_auth:read")),
):
    note = request.clinical_note or ""
    if request.coverage_eligibility_request:
        prediction = _predictor.predict_from_cer(request.coverage_eligibility_request, note)
        cer = request.coverage_eligibility_request
    elif request.clinical_note:
        extraction = _nlp.extract(
            request.clinical_note,
            "Patient/synth-patient-0000",
            "Organization/payer-aetna-synth",
        )
        prediction = _predictor.predict(extraction, note)
        cer = extraction.coverage_eligibility_request
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Provide clinical_note or coverage_eligibility_request")

    return PredictionResponse(
        approval_likelihood_score=prediction.approval_likelihood_score,
        policy_id=prediction.policy_id,
        policy_name=prediction.policy_name,
        matched_criteria=prediction.matched_criteria,
        documentation_gaps=[
            DocumentationGap(code=g.code, description=g.description, severity=g.severity)
            for g in prediction.documentation_gaps
        ],
        scoring_breakdown=prediction.scoring_breakdown,
        recommendation=prediction.recommendation,
        coverage_eligibility_request=cer,
    )
