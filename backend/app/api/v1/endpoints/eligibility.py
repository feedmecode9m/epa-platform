"""Patient eligibility endpoints."""

from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbSession, require_scope_and_permission
from app.schemas.fhir import (
    CoverageEligibilityRequestResource,
    CoverageEligibilityResponseResource,
)
from app.services.eligibility import EligibilityService

router = APIRouter()


@router.post(
    "/eligibility",
    response_model=CoverageEligibilityResponseResource,
    summary="Check patient coverage eligibility",
)
async def check_eligibility(
    request: CoverageEligibilityRequestResource,
    db: DbSession,
    user: CurrentUser = Depends(
        require_scope_and_permission("user/CoverageEligibilityRequest.write", "eligibility:check")
    ),
):
    patient_ref = request.patient.get("reference") if request.patient else None
    user.assert_patient_access(patient_ref)
    service = EligibilityService(db)
    return await service.check_eligibility(request, user_id=user.id)
