"""M00-B authentication fields.

Revision ID: 20261025_0002
Revises: 20261025_0001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261025_0002"
down_revision: str | None = "20261025_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_account ADD COLUMN IF NOT EXISTS "
        "email_verified_at TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    op.drop_column("user_account", "email_verified_at")
