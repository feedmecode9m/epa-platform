"""Initial security-hardening schema migration."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_security_hardening"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("subject_id", sa.String(255)),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("request_id", sa.String(36)),
        sa.Column("correlation_id", sa.String(36)),
        sa.Column("client_ip", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("integrity_hash", sa.String(128), nullable=False),
        sa.Column("previous_hash", sa.String(128), nullable=False),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_subject_id", "audit_logs", ["subject_id"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    op.create_table(
        "token_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jti", sa.String(36), nullable=False, unique=True),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("client_id", sa.String(255)),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("patient_id", sa.String(255)),
        sa.Column("fhir_user", sa.String(255)),
        sa.Column("launch_context", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_token_grants_jti", "token_grants", ["jti"])
    op.create_index("ix_token_grants_subject_id", "token_grants", ["subject_id"])
    op.create_index("ix_token_grants_patient_id", "token_grants", ["patient_id"])

    op.create_table(
        "oauth_authorization_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(128), nullable=False, unique=True),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column("code_challenge_method", sa.String(10), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("patient_id", sa.String(255)),
        sa.Column("launch_context", sa.Text()),
        sa.Column("state", sa.String(512)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs table is append-only (HIPAA §164.312(b))';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_no_update
            BEFORE UPDATE OR DELETE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation();")
    op.drop_table("oauth_authorization_codes")
    op.drop_table("token_grants")
    op.drop_table("audit_logs")
