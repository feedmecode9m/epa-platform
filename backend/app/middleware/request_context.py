"""Request context middleware — assigns correlation IDs for audit trail."""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_request_id_from_context() -> str:
    return request_id_ctx.get()


def get_correlation_id_from_context() -> str:
    return correlation_id_ctx.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        corr_id = request.headers.get("X-Correlation-Id") or req_id

        request_id_ctx.set(req_id)
        correlation_id_ctx.set(corr_id)
        request.state.request_id = req_id
        request.state.correlation_id = corr_id

        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        response.headers["X-Correlation-Id"] = corr_id
        return response
