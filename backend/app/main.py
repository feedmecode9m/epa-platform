"""EPA Platform FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.endpoints import oauth
from app.api.v1.router import api_router
from app.core.config import settings, validate_startup_security
from app.middleware.audit import AuditMiddleware
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.request_context import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    validate_startup_security(settings)
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.5",
        description="HIPAA-compliant electronic Prior Authorization (ePA) platform API",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    if settings.is_production:
        app.add_middleware(HTTPSRedirectMiddleware)
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-Correlation-Id"],
    )

    app.add_middleware(JWTAuthMiddleware)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.APP_NAME}

    app.include_router(oauth.router, tags=["OAuth2 / SMART"])
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()


def run() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run()
