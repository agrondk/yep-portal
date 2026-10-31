"""M01-A program catalog, offerings and rooms.

Revision ID: 20261031_0004
Revises: 20261031_0003
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261031_0004"
down_revision: str | None = "20261031_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

category = sa.Enum(
    "course",
    "camp",
    "workshop",
    "birthday",
    "team_building",
    "inclusive",
    "other",
    name="program_category",
)
delivery = sa.Enum("physical_build", "screen_based", "mixed", name="delivery_type")
program_status = sa.Enum("draft", "confirmed", "archived", name="program_status")
language = sa.Enum("sq", "en", "mixed", name="offering_language")
fee_model = sa.Enum(
    "per_child_term",
    "per_child_month",
    "per_session",
    "group_per_session",
    "free",
    "sponsored",
    name="fee_model",
)
visibility = sa.Enum("draft", "internal", "published", name="offering_visibility")


def upgrade() -> None:
    op.create_table(
        "program",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("name_sq", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("category", category, nullable=False),
        sa.Column("description_sq", sa.Text()),
        sa.Column("description_en", sa.Text()),
        sa.Column("learning_objectives_sq", sa.Text()),
        sa.Column("learning_objectives_en", sa.Text()),
        sa.Column("delivery", delivery, nullable=False),
        sa.Column("status", program_status, nullable=False),
        sa.Column("is_proposed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_account.id")),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "program_confirmation",
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.id"),
            primary_key=True,
        ),
        sa.Column("eligibility_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("duration_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("price_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "availability_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_table(
        "room",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("location.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "offering",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(160), nullable=False, unique=True),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("location.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), index=True),
        sa.Column("title_sq", sa.String(200)),
        sa.Column("title_en", sa.String(200)),
        sa.Column("language", language, nullable=False),
        sa.Column("age_min", sa.Integer(), nullable=False),
        sa.Column("age_max", sa.Integer(), nullable=False),
        sa.Column("age_reference_date", sa.Date(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("session_minutes", sa.Integer(), nullable=False),
        sa.Column("sessions_planned", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("fee_model", fee_model, nullable=False),
        sa.Column("list_price", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("visibility", visibility, nullable=False),
        sa.Column("registration_open", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("waitlist_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("age_min <= age_max", name="age_range"),
        sa.CheckConstraint("start_date <= end_date", name="date_range"),
    )
    now = datetime.now(UTC)
    programs = [
        (
            "BIG_BUILDERS",
            "big-builders",
            "Big Builders",
            "Big Builders",
            "course",
            "physical_build",
            False,
        ),
        ("ALGOBUDDY", "algobuddy", "AlgoBuddy", "AlgoBuddy", "course", "mixed", False),
        (
            "BRICKS_CHALLENGE",
            "bricks-challenge",
            "Bricks Challenge",
            "Bricks Challenge",
            "course",
            "physical_build",
            False,
        ),
        ("ALGO_PLAY", "algo-play", "Algo Play", "Algo Play", "course", "mixed", False),
        (
            "GALILEO_TECHNIC",
            "galileo-technic",
            "Galileo Technic",
            "Galileo Technic",
            "course",
            "physical_build",
            False,
        ),
        (
            "YOUNG_CODERS",
            "young-coders",
            "Young Coders",
            "Young Coders",
            "course",
            "screen_based",
            False,
        ),
        (
            "WEB_HTML_CSS",
            "web-development-html-css",
            "Web Development me HTML & CSS",
            "Web Development with HTML & CSS",
            "course",
            "screen_based",
            True,
        ),
    ]
    program_table = sa.table(
        "program",
        sa.column("id"),
        sa.column("code"),
        sa.column("slug"),
        sa.column("name_sq"),
        sa.column("name_en"),
        sa.column("category"),
        sa.column("delivery"),
        sa.column("status"),
        sa.column("is_proposed"),
        sa.column("created_at"),
    )
    confirmation_table = sa.table("program_confirmation", sa.column("program_id"))
    for code, slug, name_sq, name_en, cat, deliver, proposed in programs:
        program_id = uuid.uuid4()
        op.bulk_insert(
            program_table,
            [
                {
                    "id": program_id,
                    "code": code,
                    "slug": slug,
                    "name_sq": name_sq,
                    "name_en": name_en,
                    "category": cat,
                    "delivery": deliver,
                    "status": "draft",
                    "is_proposed": proposed,
                    "created_at": now,
                }
            ],
        )
        op.bulk_insert(confirmation_table, [{"program_id": program_id}])


def downgrade() -> None:
    op.drop_table("offering")
    op.drop_table("room")
    op.drop_table("program_confirmation")
    op.drop_table("program")
    visibility.drop(op.get_bind())
    fee_model.drop(op.get_bind())
    language.drop(op.get_bind())
    program_status.drop(op.get_bind())
    delivery.drop(op.get_bind())
    category.drop(op.get_bind())
