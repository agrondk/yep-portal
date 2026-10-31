import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.modules.core.models import Role, ScopeType


class InvitationCreate(BaseModel):
    email: EmailStr
    role: Role
    scope_type: ScopeType
    scope_id: uuid.UUID | None = None


class InvitationAccept(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=12, max_length=128)
    locale: str = Field(default="sq", pattern="^(sq|en)$")


class InvitationResponse(BaseModel):
    id: uuid.UUID
    expires_at: datetime
    development_token: str | None = None


class InvitationSummary(BaseModel):
    id: uuid.UUID
    email: str
    role: Role
    scope_type: ScopeType
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None


class LocationCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)
    address: str | None = None
    type: str = Field(pattern="^(center|school|other)$")


class LocationResponse(LocationCreate):
    id: uuid.UUID
    active: bool


class RoleAssignmentCreate(BaseModel):
    user_id: uuid.UUID
    role: Role
    scope_type: ScopeType
    scope_id: uuid.UUID | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class RoleAssignmentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: Role
    scope_type: ScopeType
    scope_id: uuid.UUID | None
    valid_from: date
    valid_to: date | None
    revoked_at: datetime | None


class UserSummary(BaseModel):
    id: uuid.UUID
    email: str
    status: str
    locale: str
    roles: list[RoleAssignmentResponse]
