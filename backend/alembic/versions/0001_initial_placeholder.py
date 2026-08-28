"""Initial schema placeholder.

Revision ID: 0001
Revises:
Create Date: 2026-08-28

Run ``alembic revision --autogenerate -m 'initial schema'`` to generate
the first migration from ORM models. Replace this placeholder afterward.

Include the following PostgreSQL trigger to enforce append-only audit logs:

    CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'audit_logs table is append-only';
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER audit_logs_no_update
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
"""

from typing import Sequence, Union

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
