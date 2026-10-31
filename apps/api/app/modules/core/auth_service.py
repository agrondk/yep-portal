import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token, verify_password
from app.modules.core.models import (
    Role,
    RoleAssignment,
    ScopeType,
    User,
    UserSession,
    UserStatus,
    VerificationToken,
)


@dataclass(frozen=True)
class IssuedToken:
    raw: str
    expires_at: datetime


PRIVILEGED_ROLES = {Role.OWNER_ADMIN, Role.FINANCE_OFFICER}


def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def register_guardian(
    db: Session, *, email: str, password: str, locale: str
) -> tuple[User, IssuedToken]:
    normalized = normalize_email(email)
    if db.scalar(select(User.id).where(User.email == normalized)) is not None:
        raise AppError(
            "EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", 409
        )

    now = now_utc()
    user = User(
        email=normalized,
        password_hash=hash_password(password),
        locale=locale,
        status=UserStatus.ACTIVE,
        mfa_enabled=False,
        created_at=now,
    )
    db.add(user)
    db.flush()
    db.add(
        RoleAssignment(
            user_id=user.id,
            role=Role.GUARDIAN,
            scope_type=ScopeType.ORGANIZATION,
            scope_id=None,
            valid_from=date.today(),
            granted_by=user.id,
            created_at=now,
        )
    )
    issued = create_verification_token(db, user, "email_verify")
    db.commit()
    return user, issued


def create_verification_token(db: Session, user: User, purpose: str) -> IssuedToken:
    settings = get_settings()
    raw = generate_token()
    expires_at = now_utc() + timedelta(minutes=settings.token_ttl_minutes)
    db.add(
        VerificationToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=hash_token(raw),
            expires_at=expires_at,
            created_at=now_utc(),
        )
    )
    return IssuedToken(raw=raw, expires_at=expires_at)


def consume_token(db: Session, *, raw_token: str, purpose: str) -> User:
    token = db.scalar(
        select(VerificationToken)
        .where(
            VerificationToken.token_hash == hash_token(raw_token),
            VerificationToken.purpose == purpose,
        )
        .with_for_update()
    )
    if token is None or token.used_at is not None or token.expires_at <= now_utc():
        raise AppError("TOKEN_INVALID", "The token is invalid or has expired.", 400)
    user = db.get(User, token.user_id)
    if user is None:
        raise AppError("TOKEN_INVALID", "The token is invalid or has expired.", 400)
    token.used_at = now_utc()
    return user


def active_roles(db: Session, user_id: uuid.UUID) -> list[Role]:
    today = date.today()
    return list(
        db.scalars(
            select(RoleAssignment.role).where(
                RoleAssignment.user_id == user_id,
                RoleAssignment.revoked_at.is_(None),
                RoleAssignment.valid_from <= today,
                (RoleAssignment.valid_to.is_(None) | (RoleAssignment.valid_to >= today)),
            )
        )
    )


def authenticate(db: Session, *, email: str, password: str, totp_code: str | None) -> User:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None or not verify_password(user.password_hash, password):
        raise AppError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
    if user.status is not UserStatus.ACTIVE or user.email_verified_at is None:
        raise AppError("ACCOUNT_NOT_READY", "Verify your email or contact an administrator.", 403)

    roles = set(active_roles(db, user.id))
    mfa_required = user.mfa_enabled or (
        get_settings().mfa_required_for_privileged and bool(roles & PRIVILEGED_ROLES)
    )
    if mfa_required:
        if not user.mfa_enabled:
            raise AppError(
                "MFA_SETUP_REQUIRED", "Multi-factor authentication setup is required.", 403
            )
        if totp_code is None or not verify_totp(user, totp_code):
            raise AppError("MFA_REQUIRED", "A valid authentication code is required.", 401)

    user.last_login_at = now_utc()
    return user


def create_session(db: Session, user: User) -> tuple[UserSession, str]:
    raw_token = generate_token()
    session = UserSession(
        token_hash=hash_token(raw_token),
        user_id=user.id,
        expires_at=now_utc() + timedelta(hours=get_settings().session_ttl_hours),
        created_at=now_utc(),
    )
    db.add(session)
    db.commit()
    return session, raw_token


def revoke_session(db: Session, session: UserSession) -> None:
    session.revoked_at = now_utc()
    db.commit()


def revoke_all_sessions(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=now_utc())
    )


def _fernet() -> Fernet:
    key = get_settings().mfa_encryption_key
    if not key:
        raise AppError("MFA_NOT_CONFIGURED", "MFA encryption is not configured.", 503)
    return Fernet(key.encode("ascii"))


def begin_mfa_setup(user: User) -> tuple[str, str]:
    secret = pyotp.random_base32()
    user.mfa_secret_enc = _fernet().encrypt(secret.encode("ascii")).decode("ascii")
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="YEP Portal")
    return secret, uri


def _mfa_secret(user: User) -> str:
    if not user.mfa_secret_enc:
        raise AppError("MFA_SETUP_REQUIRED", "Set up multi-factor authentication first.", 400)
    try:
        return _fernet().decrypt(user.mfa_secret_enc.encode("ascii")).decode("ascii")
    except InvalidToken as exc:
        raise AppError(
            "MFA_SECRET_INVALID", "Stored MFA configuration cannot be read.", 500
        ) from exc


def verify_totp(user: User, code: str) -> bool:
    return bool(pyotp.TOTP(_mfa_secret(user)).verify(code, valid_window=1))


def development_token(raw: str) -> str | None:
    return raw if get_settings().app_env == "development" else None


def constant_time_equal(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)
