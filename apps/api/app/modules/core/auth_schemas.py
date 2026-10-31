import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    locale: str = "sq"

    @field_validator("locale")
    @classmethod
    def supported_locale(cls, value: str) -> str:
        if value not in {"sq", "en"}:
            raise ValueError("Locale must be sq or en")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, pattern=r"^\d{6}$")


class TokenRequest(BaseModel):
    token: str = Field(min_length=20)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(TokenRequest):
    password: str = Field(min_length=12, max_length=128)


class MfaVerifyRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class MessageResponse(BaseModel):
    message: str
    development_token: str | None = None


class LoginResponse(BaseModel):
    user_id: uuid.UUID
    csrf_token: str


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    locale: str
    status: str
    roles: list[str]
    mfa_enabled: bool


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
