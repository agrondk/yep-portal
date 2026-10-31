"""M01-B inquiries and trial bookings.

Revision ID: 20261031_0005
Revises: 20261031_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261031_0005"
down_revision: str | None = "20261031_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

inquiry_status = sa.Enum(
    "new", "contacted", "trial_booked", "converted", "closed", name="inquiry_status"
)
trial_status = sa.Enum(
    "requested", "scheduled", "attended", "no_show", "cancelled", name="trial_status"
)


def upgrade() -> None:
    op.create_table(
        "inquiry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, index=True),
        sa.Column("phone", sa.String(50)),
        sa.Column("child_age", sa.Integer()),
        sa.Column(
            "program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("program.id"), index=True
        ),
        sa.Column("message", sa.Text()),
        sa.Column("source", sa.String(80), nullable=False, server_default="website"),
        sa.Column("utm_source", sa.String(160)),
        sa.Column("utm_medium", sa.String(160)),
        sa.Column("utm_campaign", sa.String(160)),
        sa.Column("utm_content", sa.String(160)),
        sa.Column("promo_code", sa.String(80)),
        sa.Column("heard_about_us", sa.String(160)),
        sa.Column("status", inquiry_status, nullable=False, server_default="new"),
        sa.Column(
            "assigned_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_account.id"),
            index=True,
        ),
        sa.Column("closed_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "child_age IS NULL OR child_age BETWEEN 0 AND 99", name="inquiry_child_age"
        ),
    )
    op.create_table(
        "trial_booking",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "inquiry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inquiry.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "offering_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("offering.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("date_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", trial_status, nullable=False, server_default="requested"),
        sa.Column("outcome_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trial_booking")
    op.drop_table("inquiry")
    trial_status.drop(op.get_bind())
    inquiry_status.drop(op.get_bind())
