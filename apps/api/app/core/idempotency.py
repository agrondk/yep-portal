import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.core.models import IdempotencyKey


def replay_or_none(db: Session, *, key: str, user_id: Any, route: str) -> IdempotencyKey | None:
    row = db.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.key == key,
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.route == route,
            IdempotencyKey.expires_at > datetime.now(UTC),
        )
    )
    return row


def save_response(
    db: Session,
    *,
    key: str,
    user_id: Any,
    route: str,
    body: dict[str, Any],
    status_code: int,
) -> IdempotencyKey:
    if len(key) > 255:
        raise AppError("IDEMPOTENCY_KEY_INVALID", "Idempotency key is too long.", 400)
    digest = hashlib.sha256(repr(sorted(body.items())).encode()).hexdigest()
    row = IdempotencyKey(
        key=key,
        user_id=user_id,
        route=route,
        response_hash=digest,
        response_body=body,
        status_code=status_code,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_at=datetime.now(UTC),
    )
    db.add(row)
    return row
