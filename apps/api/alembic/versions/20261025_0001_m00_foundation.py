"""M00-A foundation tables.

Revision ID: 20261025_0001
Revises: None
"""

from collections.abc import Sequence

from alembic import op
from app.core.database import Base
from app.modules.core import models  # noqa: F401

revision: str = "20261025_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    op.execute("COMMENT ON TABLE audit_event IS 'Append-only application audit history'")


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
