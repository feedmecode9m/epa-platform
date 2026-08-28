"""Durable hash-chained audit log persistence."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog

GENESIS_HASH = "GENESIS"


def compute_audit_hash(previous_hash: str, event_data: dict[str, Any]) -> str:
    payload = json.dumps(event_data, sort_keys=True, default=str)
    material = f"{previous_hash}:{payload}".encode()
    return hashlib.new(settings.AUDIT_HASH_ALGORITHM, material).hexdigest()


def compute_audit_hmac(integrity_hash: str, previous_hash: str, event_id: str) -> str:
    """HMAC-SHA256 segment for forensic non-repudiation verification."""
    message = f"{previous_hash}:{integrity_hash}:{event_id}".encode()
    return hmac.new(
        settings.AUDIT_HMAC_SECRET.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def verify_audit_entry(entry: AuditLog) -> bool:
    """Verify hash chain segment and HMAC for a stored audit record."""
    event_body = {
        "id": str(entry.id),
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else "",
        "action": entry.action,
        "outcome": entry.outcome,
        "subject_id": entry.subject_id,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id,
        "request_id": entry.request_id,
        "correlation_id": entry.correlation_id,
        "client_ip": entry.client_ip,
        "status_code": (entry.event_metadata or {}).get("status_code"),
    }
    expected_hash = compute_audit_hash(entry.previous_hash, event_body)
    if expected_hash != entry.integrity_hash:
        return False
    if entry.integrity_hmac and settings.AUDIT_HMAC_ENABLED:
        expected_hmac = compute_audit_hmac(entry.integrity_hash, entry.previous_hash, str(entry.id))
        return hmac.compare_digest(expected_hmac, entry.integrity_hmac)
    return True


class AuditChainService:
    """Append-only audit writer with cryptographic hash chaining."""

    async def get_chain_head(self, session: AsyncSession) -> str:
        result = await session.execute(
            select(AuditLog.integrity_hash)
            .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
            .limit(1)
        )
        head = result.scalar_one_or_none()
        return head or GENESIS_HASH

    async def append(
        self,
        session: AsyncSession,
        *,
        action: str,
        outcome: str,
        subject_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        event_metadata: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> AuditLog:
        previous_hash = await self.get_chain_head(session)
        event_id = uuid.uuid4()

        event_body = {
            "id": str(event_id),
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "outcome": outcome,
            "subject_id": subject_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "client_ip": client_ip,
            "status_code": status_code,
        }
        integrity_hash = compute_audit_hash(previous_hash, event_body)
        integrity_hmac = (
            compute_audit_hmac(integrity_hash, previous_hash, str(event_id))
            if settings.AUDIT_HMAC_ENABLED
            else None
        )

        meta = dict(event_metadata or {})
        if status_code is not None:
            meta["status_code"] = status_code

        entry = AuditLog(
            id=event_id,
            action=action,
            outcome=outcome,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            correlation_id=correlation_id,
            client_ip=client_ip,
            user_agent=user_agent,
            event_metadata=meta or None,
            integrity_hash=integrity_hash,
            previous_hash=previous_hash,
            integrity_hmac=integrity_hmac,
        )
        session.add(entry)
        await session.commit()
        return entry

    async def append_from_middleware(self, **kwargs: Any) -> AuditLog | None:
        """Write audit entry using an independent session (middleware-safe)."""
        try:
            async with AsyncSessionLocal() as session:
                return await self.append(session, **kwargs)
        except Exception:
            return None


audit_chain_service = AuditChainService()
