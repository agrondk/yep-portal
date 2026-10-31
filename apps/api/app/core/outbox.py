from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import OutboxMessage


def enqueue(
    session: Session,
    *,
    template_key: str,
    locale: str,
    payload: dict[str, Any],
    dedupe_key: str,
    recipient_email: str | None = None,
    recipient_user_id: Any = None,
    channel: str = "email",
) -> OutboxMessage:
    existing = session.scalar(select(OutboxMessage).where(OutboxMessage.dedupe_key == dedupe_key))
    if existing is not None:
        return existing
    row = OutboxMessage(
        channel=channel,
        template_key=template_key,
        locale=locale,
        recipient_user_id=recipient_user_id,
        recipient_email=recipient_email,
        payload=payload,
        dedupe_key=dedupe_key,
        status="queued",
        attempts=0,
        created_at=datetime.now(UTC),
    )
    session.add(row)
    return row
