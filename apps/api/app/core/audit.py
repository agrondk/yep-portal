import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.modules.core.models import AuditEvent

REDACTED_FIELDS = {"password", "password_hash", "token", "token_hash", "mfa_secret_enc"}


@dataclass(frozen=True)
class AuditInput:
    action: str
    actor_id: uuid.UUID | None = None
    actor_type: str = "user"
    role: str | None = None
    scope_refs: dict[str, Any] = field(default_factory=dict)
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    subject_refs: dict[str, Any] = field(default_factory=dict)
    outcome: str = "succeeded"
    reason: str | None = None
    changed_fields: dict[str, Any] = field(default_factory=dict)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)


def _redact(values: dict[str, Any]) -> dict[str, Any]:
    return {key: "[REDACTED]" if key in REDACTED_FIELDS else value for key, value in values.items()}


def record(session: Session, event: AuditInput) -> AuditEvent:
    row = AuditEvent(
        occurred_at=datetime.now(UTC),
        actor_id=event.actor_id,
        actor_type=event.actor_type,
        role=event.role,
        scope_refs=event.scope_refs,
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        subject_refs=event.subject_refs,
        outcome=event.outcome,
        reason=event.reason,
        changed_fields=_redact(event.changed_fields),
        correlation_id=event.correlation_id,
    )
    session.add(row)
    return row


def record_failure(event: AuditInput) -> None:
    """Persist denied/failed events independently from the request transaction."""
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    isolated = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with isolated.begin() as session:
        record(session, event)
    engine.dispose()
