import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.core.models import TimestampMixin, uuid_pk


class ProgramCategory(enum.StrEnum):
    COURSE = "course"
    CAMP = "camp"
    WORKSHOP = "workshop"
    BIRTHDAY = "birthday"
    TEAM_BUILDING = "team_building"
    INCLUSIVE = "inclusive"
    OTHER = "other"


class DeliveryType(enum.StrEnum):
    PHYSICAL_BUILD = "physical_build"
    SCREEN_BASED = "screen_based"
    MIXED = "mixed"


class ProgramStatus(enum.StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class OfferingLanguage(enum.StrEnum):
    SQ = "sq"
    EN = "en"
    MIXED = "mixed"


class FeeModel(enum.StrEnum):
    PER_CHILD_TERM = "per_child_term"
    PER_CHILD_MONTH = "per_child_month"
    PER_SESSION = "per_session"
    GROUP_PER_SESSION = "group_per_session"
    FREE = "free"
    SPONSORED = "sponsored"


class OfferingVisibility(enum.StrEnum):
    DRAFT = "draft"
    INTERNAL = "internal"
    PUBLISHED = "published"


class Program(Base, TimestampMixin):
    __tablename__ = "program"
    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name_sq: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    category: Mapped[ProgramCategory] = mapped_column(
        Enum(
            ProgramCategory,
            name="program_category",
            values_callable=lambda items: [item.value for item in items],
        )
    )
    description_sq: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    learning_objectives_sq: Mapped[str | None] = mapped_column(Text)
    learning_objectives_en: Mapped[str | None] = mapped_column(Text)
    delivery: Mapped[DeliveryType] = mapped_column(
        Enum(
            DeliveryType,
            name="delivery_type",
            values_callable=lambda items: [item.value for item in items],
        )
    )
    status: Mapped[ProgramStatus] = mapped_column(
        Enum(
            ProgramStatus,
            name="program_status",
            values_callable=lambda items: [item.value for item in items],
        )
    )
    is_proposed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_account.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmation: Mapped["ProgramConfirmation"] = relationship(
        back_populates="program", cascade="all, delete-orphan", uselist=False
    )


class ProgramConfirmation(Base):
    __tablename__ = "program_confirmation"
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("program.id"), primary_key=True)
    eligibility_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    price_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    availability_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    program: Mapped[Program] = relationship(back_populates="confirmation")


class Room(Base, TimestampMixin):
    __tablename__ = "room"
    id: Mapped[uuid.UUID] = uuid_pk()
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("location.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    capacity: Mapped[int] = mapped_column(Integer)


class Offering(Base, TimestampMixin):
    __tablename__ = "offering"
    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("program.id"), index=True)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("location.id"), index=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    title_sq: Mapped[str | None] = mapped_column(String(200))
    title_en: Mapped[str | None] = mapped_column(String(200))
    language: Mapped[OfferingLanguage] = mapped_column(
        Enum(
            OfferingLanguage,
            name="offering_language",
            values_callable=lambda items: [item.value for item in items],
        )
    )
    age_min: Mapped[int] = mapped_column(Integer)
    age_max: Mapped[int] = mapped_column(Integer)
    age_reference_date: Mapped[date] = mapped_column(Date)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    session_minutes: Mapped[int] = mapped_column(Integer)
    sessions_planned: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    fee_model: Mapped[FeeModel] = mapped_column(
        Enum(
            FeeModel,
            name="fee_model",
            values_callable=lambda items: [item.value for item in items],
        )
    )
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    visibility: Mapped[OfferingVisibility] = mapped_column(
        Enum(
            OfferingVisibility,
            name="offering_visibility",
            values_callable=lambda items: [item.value for item in items],
        )
    )
    registration_open: Mapped[bool] = mapped_column(Boolean, default=False)
    waitlist_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    program: Mapped[Program] = relationship()
