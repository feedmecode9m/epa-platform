"""Immutable audit logging middleware with durable hash-chained persistence."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_context import get_correlation_id_from_context, get_request_id_from_context
from app.services.audit_chain import audit_chain_service


class AuditMiddleware(BaseHTTPMiddleware):
    """Captures API access events and persists append-only audit records."""

    AUDITED_PATHS = ("/api/v1/",)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        should_audit = any(request.url.path.startswith(p) for p in self.AUDITED_PATHS)
        audit_event_id = str(uuid.uuid4())

        response = await call_next(request)

        if should_audit:
            entry = await audit_chain_service.append_from_middleware(
                action=f"{request.method} {request.url.path}",
                outcome="success" if response.status_code < 400 else "failure",
                subject_id=getattr(request.state, "user_id", None),
                resource_type=getattr(request.state, "resource_type", None),
                resource_id=getattr(request.state, "resource_id", None),
                request_id=get_request_id_from_context(),
                correlation_id=get_correlation_id_from_context(),
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                status_code=response.status_code,
            )
            if entry:
                audit_event_id = str(entry.id)
                request.state.audit_event_id = audit_event_id

        response.headers["X-Audit-Event-Id"] = audit_event_id
        return response
