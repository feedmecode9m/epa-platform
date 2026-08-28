"""Audit log service — append-only writes with hash chaining."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.audit_chain import audit_chain_service


class AuditService:
    """Service for explicit audit log entries beyond middleware coverage."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log_event(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        subject_id: str | None = None,
        outcome: str = "success",
        event_metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append an immutable audit log entry. Never stores PHI content."""
        return await audit_chain_service.append(
            self._db,
            action=action,
            outcome=outcome,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=event_metadata,
        )
