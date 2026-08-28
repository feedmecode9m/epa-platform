"""Add HMAC signature column to audit_logs."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_audit_hmac"
down_revision: Union[str, None] = "0002_security_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("integrity_hmac", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "integrity_hmac")
