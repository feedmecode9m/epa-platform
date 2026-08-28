"""Prior authorization request tracking model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PriorAuthStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    APPROVED = "approved"
    DENIED = "denied"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"


class PriorAuthorization(Base):
    __tablename__ = "prior_authorizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=PriorAuthStatus.DRAFT.value)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    submitted_by: Mapped[str] = mapped_column(String(255))

    # FHIR resources stored as JSONB (PHI within — DB-level encryption required)
    claim_resource: Mapped[dict] = mapped_column(JSONB, nullable=False)
    claim_response_resource: Mapped[dict | None] = mapped_column(JSONB)

    payer_reference: Mapped[str | None] = mapped_column(String(255))
    pre_auth_ref: Mapped[str | None] = mapped_column(String(255))
    disposition: Mapped[str | None] = mapped_column(Text)

    # AI prediction (non-PHI structured output)
    ai_approval_score: Mapped[float | None] = mapped_column(Float)
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    ai_model_version: Mapped[str | None] = mapped_column(String(50))
    ai_factors: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
