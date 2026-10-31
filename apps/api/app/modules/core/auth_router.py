from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.core.rate_limit import rate_limiter
from app.core.security import generate_csrf_token, hash_password
from app.modules.core.auth_dependencies import AuthContext, current_auth, require_csrf
from app.modules.core.auth_schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MessageResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenRequest,
)
from app.modules.core.auth_service import (
    active_roles,
    authenticate,
    begin_mfa_setup,
    consume_token,
    create_session,
    create_verification_token,
    development_token,
    normalize_email,
    register_guardian,
    revoke_all_sessions,
    revoke_session,
    verify_totp,
)
from app.modules.core.models import User

router = APIRouter(tags=["authentication"])


def client_key(request: Request, action: str, subject: str = "") -> str:
    host = request.client.host if request.client else "unknown"
    return f"{action}:{host}:{subject.casefold()}"


def set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "yep_session",
        session_token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
        path="/",
    )
    response.set_cookie(
        "yep_csrf",
        csrf_token,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
        path="/",
    )


@router.post("/auth/register", response_model=MessageResponse, status_code=201)
def register(
    body: RegisterRequest, request: Request, db: Session = Depends(get_db)
) -> MessageResponse:
    rate_limiter.check(
        client_key(request, "register", str(body.email)), limit=5, window_seconds=3600
    )
    _user, issued = register_guardian(
        db, email=str(body.email), password=body.password, locale=body.locale
    )
    return MessageResponse(
        message="Registration received. Check your email to verify the account.",
        development_token=development_token(issued.raw),
    )


@router.post("/auth/verify-email", response_model=MessageResponse)
def verify_email(body: TokenRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = consume_token(db, raw_token=body.token, purpose="email_verify")
    from app.modules.core.auth_service import now_utc

    user.email_verified_at = now_utc()
    db.commit()
    return MessageResponse(message="Email verified.")


@router.post("/auth/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    rate_limiter.check(client_key(request, "login", str(body.email)), limit=10, window_seconds=900)
    user = authenticate(db, email=str(body.email), password=body.password, totp_code=body.totp_code)
    _session, raw_session = create_session(db, user)
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, raw_session, csrf_token)
    return LoginResponse(user_id=user.id, csrf_token=csrf_token)


@router.post("/auth/logout", response_model=MessageResponse)
def logout(
    response: Response,
    auth: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> MessageResponse:
    revoke_session(db, auth.session)
    response.delete_cookie("yep_session", path="/")
    response.delete_cookie("yep_csrf", path="/")
    return MessageResponse(message="Signed out.")


@router.post("/auth/password/forgot", response_model=MessageResponse)
def forgot_password(
    body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)
) -> MessageResponse:
    rate_limiter.check(client_key(request, "forgot", str(body.email)), limit=5, window_seconds=3600)
    user = db.scalar(select(User).where(User.email == normalize_email(str(body.email))))
    issued = create_verification_token(db, user, "password_reset") if user else None
    if issued:
        db.commit()
    return MessageResponse(
        message="If the account exists, password reset instructions have been sent.",
        development_token=development_token(issued.raw) if issued else None,
    )


@router.post("/auth/password/reset", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = consume_token(db, raw_token=body.token, purpose="password_reset")
    user.password_hash = hash_password(body.password)
    revoke_all_sessions(db, user.id)
    db.commit()
    return MessageResponse(message="Password reset. You can now sign in.")


@router.get("/me", response_model=MeResponse)
def me(auth: AuthContext = Depends(current_auth), db: Session = Depends(get_db)) -> MeResponse:
    return MeResponse(
        id=auth.user.id,
        email=auth.user.email,
        locale=auth.user.locale,
        status=auth.user.status.value,
        roles=[role.value for role in active_roles(db, auth.user.id)],
        mfa_enabled=auth.user.mfa_enabled,
    )


@router.post("/auth/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(
    auth: AuthContext = Depends(require_csrf), db: Session = Depends(get_db)
) -> MfaSetupResponse:
    secret, uri = begin_mfa_setup(auth.user)
    auth.user.mfa_enabled = False
    db.commit()
    return MfaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/auth/mfa/verify", response_model=MessageResponse)
def mfa_verify(
    body: MfaVerifyRequest,
    auth: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if not verify_totp(auth.user, body.code):
        raise AppError("MFA_CODE_INVALID", "The authentication code is invalid.", 400)
    auth.user.mfa_enabled = True
    db.commit()
    return MessageResponse(message="Multi-factor authentication enabled.")
