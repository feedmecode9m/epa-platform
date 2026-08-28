"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_MARKERS = {
    "change_me",
    "changeme",
    "change_me_to_a_secure_random_value_min_32_chars",
    "CHANGE_ME",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "ePA Platform"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "postgresql+asyncpg://epa:changeme@localhost:5432/epa_platform"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    JWT_KEY_ID: str = "epa-platform-rs256-v1"
    JWT_PRIVATE_KEY_PATH: str = "keys/jwt_private.pem"
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OAUTH_ISSUER: str = "https://api.epa-platform.example.com"
    OAUTH_AUDIENCE: str = "https://api.epa-platform.example.com"

    OAUTH2_ENABLED: bool = False
    OAUTH2_ISSUER_URL: str | None = None
    OAUTH2_CLIENT_ID: str | None = None
    OAUTH2_CLIENT_SECRET: str | None = None
    OAUTH2_JWKS_URL: str | None = None

    # Registered SMART clients (client_id -> secret); production uses vault
    OAUTH_CLIENTS: dict[str, str] = Field(default_factory=lambda: {"epa-smart-client": "dev-secret-change-me"})

    PHI_ENCRYPTION_KEY_ID: str = "arn:aws:kms:us-east-1:000000000000:key/mock-cmk"
    PHI_ENCRYPTION_ALGORITHM: str = "AES-256-GCM"

    AUDIT_LOG_IMMUTABLE: bool = True
    AUDIT_HASH_ALGORITHM: str = "SHA-256"
    AUDIT_HMAC_SECRET: str = Field(default="dev-audit-hmac-secret-change-in-production")
    AUDIT_HMAC_ENABLED: bool = True

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.APP_ENV in {"staging", "production"}:
            for client_id, secret in self.OAUTH_CLIENTS.items():
                if secret.lower() in INSECURE_SECRET_MARKERS or "change" in secret.lower():
                    raise ValueError(
                        f"Insecure OAuth client secret for '{client_id}' in {self.APP_ENV}"
                    )
        return self


def validate_startup_security(settings: Settings) -> None:
    """Fail fast when insecure defaults are detected in non-development environments."""
    if settings.APP_ENV == "development":
        return
    for _client_id, secret in settings.OAUTH_CLIENTS.items():
        if any(marker in secret for marker in INSECURE_SECRET_MARKERS):
            raise RuntimeError("Refusing to start: insecure OAuth client secrets configured")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
