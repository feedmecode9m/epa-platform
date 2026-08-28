"""JWT authentication middleware with JWKS signature verification."""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import TokenValidationError, verify_access_token_signature

logger = logging.getLogger(__name__)

PUBLIC_PATHS: set[str] = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/.well-known/smart-configuration",
    "/.well-known/jwks.json",
    "/oauth/authorize",
    "/oauth/token",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Verify JWT cryptographic signature; grant resolution occurs in dependencies."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        if path in {"/oauth/introspect", "/oauth/revoke"}:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            claims = verify_access_token_signature(token)
            request.state.user_id = claims.get("sub")
            request.state.token_jti = claims.get("jti")
        except TokenValidationError:
            logger.warning("JWT signature validation failed")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
