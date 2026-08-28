"""Prior authorization business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prior_auth import PriorAuthStatus, PriorAuthorization
from app.schemas.fhir import (
    ApprovalLikelihood,
    PriorAuthRequestBundle,
    PriorAuthStatusResponse,
)


class PriorAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_request(self, bundle: PriorAuthRequestBundle, submitted_by: str) -> dict:
        tracking_id = str(uuid.uuid4())
        claim_entry = next(
            (e for e in bundle.entry if e.get("resource", {}).get("resourceType") == "Claim"),
            None,
        )
        if not claim_entry:
            raise ValueError("Bundle must contain a Claim resource")

        record = PriorAuthorization(
            tracking_id=tracking_id,
            status=PriorAuthStatus.PENDING.value,
            patient_id=uuid.uuid4(),  # TODO: resolve from bundle Patient reference
            submitted_by=submitted_by,
            claim_resource=claim_entry["resource"],
        )
        self.db.add(record)
        await self.db.flush()

        # TODO: Enqueue AI prediction job, payer submission
        return {
            "trackingId": tracking_id,
            "status": PriorAuthStatus.PENDING.value,
            "location": f"/api/v1/prior-authorization/status/{tracking_id}",
        }

    async def get_status(self, tracking_id: uuid.UUID) -> PriorAuthStatusResponse:
        # TODO: Query DB by tracking_id
        return PriorAuthStatusResponse(
            tracking_id=tracking_id,
            status=PriorAuthStatus.PENDING,
            patient_id=None,
            last_updated=datetime.now(UTC),
            ai_prediction=ApprovalLikelihood(
                score=0.72,
                confidence=0.85,
                model_version="pa-likelihood-v0.1.0-placeholder",
                generated_at=datetime.now(UTC),
            ),
        )
