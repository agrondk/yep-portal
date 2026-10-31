"""M01-C frequently asked questions.

Revision ID: 20261101_0006
Revises: 20261031_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261101_0006"
down_revision: str | None = "20261031_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faq",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_sq", sa.String(500), nullable=False),
        sa.Column("question_en", sa.String(500), nullable=False),
        sa.Column("answer_sq", sa.Text(), nullable=False),
        sa.Column("answer_en", sa.Text(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("faq")
