from dataclasses import dataclass

from fastapi import Cookie, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import hash_token
from app.modules.core.auth_service import constant_time_equal, now_utc
from app.modules.core.models import User, UserSession, UserStatus


@dataclass
class AuthContext:
    user: User
    session: UserSession


def current_auth(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias="yep_session"),
) -> AuthContext:
    if not session_token:
        raise AppError("AUTH_REQUIRED", "Authentication is required.", 401)
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_token(session_token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now_utc(),
        )
    )
    if session is None:
        raise AppError("SESSION_INVALID", "Your session has expired.", 401)
    user = db.get(User, session.user_id)
    if user is None or user.status is not UserStatus.ACTIVE:
        raise AppError("ACCESS_REVOKED", "This account is not active.", 403)
    return AuthContext(user=user, session=session)


def require_csrf(
    auth: AuthContext = Depends(current_auth),
    csrf_cookie: str | None = Cookie(default=None, alias="yep_csrf"),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> AuthContext:
    if not csrf_cookie or not csrf_header or not constant_time_equal(csrf_cookie, csrf_header):
        raise AppError("CSRF_INVALID", "The CSRF token is missing or invalid.", 403)
    return auth
