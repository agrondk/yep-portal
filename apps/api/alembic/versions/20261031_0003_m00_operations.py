"""M00-D operational services.

Revision ID: 20261031_0003
Revises: 20261025_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261031_0003"
down_revision: str | None = "20261025_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE idempotency_key ADD COLUMN IF NOT EXISTS "
        "response_body JSONB NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        "ALTER TABLE idempotency_key ADD COLUMN IF NOT EXISTS "
        "status_code INTEGER NOT NULL DEFAULT 200"
    )
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'yep_app') THEN
            REVOKE UPDATE, DELETE ON audit_event FROM yep_app;
          END IF;
        END $$
        """
    )


def downgrade() -> None:
    op.drop_column("idempotency_key", "status_code")
    op.drop_column("idempotency_key", "response_body")
