import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token
from app.modules.core.auth_service import development_token, normalize_email
from app.modules.core.models import (
    Invitation,
    Role,
    RoleAssignment,
    ScopeType,
    User,
    UserStatus,
)


def invite_user(
    db: Session,
    *,
    email: str,
    role: Role,
    scope_type: ScopeType,
    scope_id: uuid.UUID | None,
    invited_by: User,
) -> tuple[Invitation, str | None]:
    now = datetime.now(UTC)
    raw = generate_token()
    invitation = Invitation(
        email=normalize_email(email),
        role=role,
        scope_type=scope_type,
        scope_id=scope_id,
        token_hash=hash_token(raw),
        expires_at=now + timedelta(days=get_settings().invitation_ttl_days),
        invited_by=invited_by.id,
        created_at=now,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation, development_token(raw)


def accept_invitation(
    db: Session, *, token: str, password: str, locale: str
) -> tuple[User, RoleAssignment]:
    now = datetime.now(UTC)
    invitation = db.scalar(
        select(Invitation).where(Invitation.token_hash == hash_token(token)).with_for_update()
    )
    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise AppError("INVITATION_INVALID", "The invitation is invalid or has expired.", 400)
    user = db.scalar(select(User).where(User.email == invitation.email))
    if user is None:
        user = User(
            email=invitation.email,
            password_hash=hash_password(password),
            locale=locale,
            status=UserStatus.ACTIVE,
            email_verified_at=now,
            mfa_enabled=False,
            created_at=now,
        )
        db.add(user)
        db.flush()
    elif user.status is UserStatus.DISABLED:
        raise AppError("ACCOUNT_DISABLED", "This account is disabled.", 403)
    assignment = RoleAssignment(
        user_id=user.id,
        role=invitation.role,
        scope_type=invitation.scope_type,
        scope_id=invitation.scope_id,
        valid_from=date.today(),
        granted_by=invitation.invited_by,
        created_at=now,
    )
    invitation.accepted_at = now
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return user, assignment
