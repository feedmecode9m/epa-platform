"""Server-side OAuth token grant records — source of truth for scopes and roles."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TokenGrant(Base):
    """Immutable-at-issuance grant bound to JWT ``jti``.

    Scopes and roles are assigned server-side at token issuance and resolved
    at request time — never trusted from JWT claims alone.
    """

    __tablename__ = "token_grants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_id: Mapped[str | None] = mapped_column(String(255))
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    patient_id: Mapped[str | None] = mapped_column(String(255), index=True)
    fhir_user: Mapped[str | None] = mapped_column(String(255))
    launch_context: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OAuthAuthorizationCode(Base):
    """Short-lived authorization code with PKCE binding."""

    __tablename__ = "oauth_authorization_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    code_challenge: Mapped[str] = mapped_column(String(128), nullable=False)
    code_challenge_method: Mapped[str] = mapped_column(String(10), default="S256", nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_id: Mapped[str | None] = mapped_column(String(255))
    launch_context: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(String(512))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
