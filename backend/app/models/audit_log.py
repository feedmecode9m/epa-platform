"""Append-only immutable audit log model.

HIPAA requires audit trails that cannot be modified or deleted.
Enforce via DB triggers and application-layer guards.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_id: Mapped[str | None] = mapped_column(String(255))
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    request_id: Mapped[str | None] = mapped_column(String(36))
    correlation_id: Mapped[str | None] = mapped_column(String(36))
    client_ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    integrity_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    integrity_hmac: Mapped[str | None] = mapped_column(String(128))

    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_subject_id", "subject_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        # Append-only: no UPDATE or DELETE triggers to be added in migration
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} {self.action}>"
