"""Patient record model — PHI fields encrypted at rest."""

import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PatientRecord(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fhir_patient_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # PHI — encrypted at rest via PHIEncryptionService before persistence
    encrypted_name: Mapped[str | None] = mapped_column(String(512))
    encrypted_dob: Mapped[str | None] = mapped_column(String(512))
    encrypted_ssn_last4: Mapped[str | None] = mapped_column(String(512))
    encrypted_address: Mapped[str | None] = mapped_column(String(1024))
    encrypted_phone: Mapped[str | None] = mapped_column(String(512))

    # Non-PHI searchable token (HMAC of MRN for lookup without decryption)
    mrn_token: Mapped[str | None] = mapped_column(String(128), index=True)

    gender: Mapped[str | None] = mapped_column(String(20))
    fhir_resource: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Decrypted DOB populated by service layer after PHI decryption (not persisted).
