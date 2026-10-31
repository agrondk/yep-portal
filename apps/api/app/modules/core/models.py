import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import CITEXT, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserStatus(str, enum.Enum):
    INVITED = "invited"
    ACTIVE = "active"
    DISABLED = "disabled"


class Role(str, enum.Enum):
    OWNER_ADMIN = "owner_admin"
    OPERATIONS_COORDINATOR = "operations_coordinator"
    INSTRUCTOR = "instructor"
    FINANCE_OFFICER = "finance_officer"
    MARKETING_COORDINATOR = "marketing_coordinator"
    GUARDIAN = "guardian"
    STUDENT = "student"
    SCHOOL_COORDINATOR = "school_coordinator"
    SPONSOR = "sponsor"


class ScopeType(str, enum.Enum):
    ORGANIZATION = "organization"
    LOCATION = "location"
    PARTNER = "partner"
    PROGRAM = "program"
    COHORT = "cohort"
    INITIATIVE = "initiative"
    HOUSEHOLD = "household"


class Organization(Base, TimestampMixin):
    __tablename__ = "organization"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Belgrade")
    default_locale: Mapped[str] = mapped_column(String(5), default="sq")
    reporting_year_start_month: Mapped[int] = mapped_column(default=1)


class Location(Base, TimestampMixin):
    __tablename__ = "location"
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id"))
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(default=True)


class User(Base, TimestampMixin):
    __tablename__ = "user_account"
    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(CITEXT(), unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    locale: Mapped[str] = mapped_column(String(5), default="sq")
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus, name="user_status"))
    mfa_secret_enc: Mapped[str | None] = mapped_column(Text)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(Base, TimestampMixin):
    __tablename__ = "user_session"
    id: Mapped[uuid.UUID] = uuid_pk()
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(INET())
    user_agent: Mapped[str | None] = mapped_column(Text)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RoleAssignment(Base, TimestampMixin):
    __tablename__ = "role_assignment"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"), index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role_name"))
    scope_type: Mapped[ScopeType] = mapped_column(Enum(ScopeType, name="scope_type"))
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    granted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Invitation(Base, TimestampMixin):
    __tablename__ = "invitation"
    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(CITEXT())
    role: Mapped[Role] = mapped_column(Enum(Role, name="role_name"))
    scope_type: Mapped[ScopeType] = mapped_column(Enum(ScopeType, name="scope_type"))
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invited_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))


class VerificationToken(Base, TimestampMixin):
    __tablename__ = "verification_token"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(30))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = (
        Index("ix_audit_event_entity", "entity_type", "entity_id"),
        Index("ix_audit_event_actor_id", "actor_id"),
        Index("ix_audit_event_outcome", "outcome"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_type: Mapped[str] = mapped_column(String(20))
    role: Mapped[str | None] = mapped_column(String(40))
    scope_refs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str | None] = mapped_column(String(80))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    subject_refs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    outcome: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(Text)
    changed_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)


class IdempotencyKey(Base, TimestampMixin):
    __tablename__ = "idempotency_key"
    __table_args__ = (UniqueConstraint("key", "user_id", "route"),)
    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))
    route: Mapped[str] = mapped_column(String(255))
    response_hash: Mapped[str] = mapped_column(String(64))
    response_body: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status_code: Mapped[int] = mapped_column(default=200)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FileObject(Base, TimestampMixin):
    __tablename__ = "file_object"
    id: Mapped[uuid.UUID] = uuid_pk()
    bucket: Mapped[str] = mapped_column(String(100))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(150))
    size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    owner_entity_type: Mapped[str] = mapped_column(String(80))
    owner_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))
    scope_refs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OutboxMessage(Base, TimestampMixin):
    __tablename__ = "outbox_message"
    id: Mapped[uuid.UUID] = uuid_pk()
    channel: Mapped[str] = mapped_column(String(20))
    template_key: Mapped[str] = mapped_column(String(100))
    locale: Mapped[str] = mapped_column(String(5))
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_account.id"))
    recipient_email: Mapped[str | None] = mapped_column(CITEXT())
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(20))
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobRun(Base):
    __tablename__ = "job_run"
    id: Mapped[uuid.UUID] = uuid_pk()
    job_name: Mapped[str] = mapped_column(String(150), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(20))
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Setting(Base):
    __tablename__ = "setting"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_account.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
