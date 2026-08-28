"""Coverage eligibility business logic."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.fhir import (
    CoverageEligibilityRequestResource,
    CoverageEligibilityResponseResource,
)


class EligibilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_eligibility(
        self,
        request: CoverageEligibilityRequestResource,
        user_id: str,
    ) -> CoverageEligibilityResponseResource:
        # TODO: Forward to payer FHIR endpoint, persist request/response
        return CoverageEligibilityResponseResource(
            id=str(datetime.now(UTC).timestamp()).replace(".", ""),
            status="active",
            outcome="complete",
            patient=request.patient,
            insurer=request.insurer,
            insurance=[
                {
                    "inforce": True,
                    "item": [
                        {
                            "name": "General Coverage",
                            "authorizationRequired": True,
                            "benefit": [{"type": {"text": "Prior Authorization Required"}}],
                        }
                    ],
                }
            ],
        )
