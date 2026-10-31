import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authorization import PermissionContext, ScopeService, require_permission
from app.core.database import get_db
from app.core.errors import AppError
from app.modules.core.access_schemas import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    InvitationSummary,
    LocationCreate,
    LocationResponse,
    RoleAssignmentCreate,
    RoleAssignmentResponse,
    UserSummary,
)
from app.modules.core.access_service import accept_invitation, invite_user
from app.modules.core.models import Invitation, Location, RoleAssignment, ScopeType, User

router = APIRouter(tags=["access control"])


def assignment_response(item: RoleAssignment) -> RoleAssignmentResponse:
    return RoleAssignmentResponse.model_validate(item, from_attributes=True)


@router.get("/admin/users", response_model=list[UserSummary])
def list_users(
    permission: PermissionContext = Depends(require_permission("core.user.view")),
    db: Session = Depends(get_db),
) -> list[UserSummary]:
    users = list(db.scalars(select(User).order_by(User.email)))
    assignments = list(
        db.scalars(select(RoleAssignment).where(RoleAssignment.revoked_at.is_(None)))
    )
    by_user: dict[uuid.UUID, list[RoleAssignment]] = {}
    for item in assignments:
        by_user.setdefault(item.user_id, []).append(item)
    unrestricted = any(
        item.role.value == "owner_admin"
        and item.scope_type.value == "organization"
        and item.scope_id is None
        for item in permission.assignments
    )
    visible_user_ids = {
        item.user_id
        for item in assignments
        if unrestricted or ScopeService.can_manage_scope(permission, item.scope_type, item.scope_id)
    }
    return [
        UserSummary(
            id=user.id,
            email=user.email,
            status=user.status.value,
            locale=user.locale,
            roles=[assignment_response(item) for item in by_user.get(user.id, [])],
        )
        for user in users
        if user.id in visible_user_ids
    ]


@router.post("/admin/invitations", response_model=InvitationResponse, status_code=201)
def create_invitation(
    body: InvitationCreate,
    permission: PermissionContext = Depends(require_permission("core.invitation.create")),
    db: Session = Depends(get_db),
) -> InvitationResponse:
    ScopeService.assert_scope_grantable(permission, body.scope_type, body.scope_id)
    invitation, dev_token = invite_user(
        db,
        email=str(body.email),
        role=body.role,
        scope_type=body.scope_type,
        scope_id=body.scope_id,
        invited_by=permission.auth.user,
    )
    return InvitationResponse(
        id=invitation.id,
        expires_at=invitation.expires_at,
        development_token=dev_token,
    )


@router.get("/admin/invitations", response_model=list[InvitationSummary])
def list_invitations(
    _permission: PermissionContext = Depends(require_permission("core.invitation.view")),
    db: Session = Depends(get_db),
) -> list[InvitationSummary]:
    rows = db.scalars(select(Invitation).order_by(Invitation.created_at.desc()).limit(100))
    return [InvitationSummary.model_validate(row, from_attributes=True) for row in rows]


@router.get("/admin/locations", response_model=list[LocationResponse])
def list_locations(
    permission: PermissionContext = Depends(require_permission("core.location.view")),
    db: Session = Depends(get_db),
) -> list[LocationResponse]:
    statement = ScopeService.filter(permission, select(Location), Location)
    return [
        LocationResponse.model_validate(row, from_attributes=True) for row in db.scalars(statement)
    ]


@router.post("/admin/locations", response_model=LocationResponse, status_code=201)
def create_location(
    body: LocationCreate,
    permission: PermissionContext = Depends(require_permission("core.location.create")),
    db: Session = Depends(get_db),
) -> LocationResponse:
    ScopeService.assert_scope_grantable(permission, ScopeType.ORGANIZATION, None)
    row = Location(
        organization_id=body.organization_id,
        name=body.name,
        address=body.address,
        type=body.type,
        active=True,
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LocationResponse.model_validate(row, from_attributes=True)


@router.post("/invitations/accept", response_model=RoleAssignmentResponse)
def redeem_invitation(
    body: InvitationAccept, db: Session = Depends(get_db)
) -> RoleAssignmentResponse:
    _user, assignment = accept_invitation(
        db, token=body.token, password=body.password, locale=body.locale
    )
    return assignment_response(assignment)


@router.post("/admin/role-assignments", response_model=RoleAssignmentResponse, status_code=201)
def grant_role(
    body: RoleAssignmentCreate,
    permission: PermissionContext = Depends(require_permission("core.user.create")),
    db: Session = Depends(get_db),
) -> RoleAssignmentResponse:
    ScopeService.assert_scope_grantable(permission, body.scope_type, body.scope_id)
    if db.get(User, body.user_id) is None:
        raise AppError("USER_NOT_FOUND", "User not found.", 404)
    assignment = RoleAssignment(
        user_id=body.user_id,
        role=body.role,
        scope_type=body.scope_type,
        scope_id=body.scope_id,
        valid_from=body.valid_from or date.today(),
        valid_to=body.valid_to,
        granted_by=permission.auth.user.id,
        created_at=datetime.now(UTC),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment_response(assignment)


@router.delete("/admin/role-assignments/{assignment_id}", response_model=RoleAssignmentResponse)
def revoke_role(
    assignment_id: uuid.UUID,
    permission: PermissionContext = Depends(require_permission("core.user.edit")),
    db: Session = Depends(get_db),
) -> RoleAssignmentResponse:
    assignment = db.get(RoleAssignment, assignment_id)
    if assignment is None:
        raise AppError("ROLE_ASSIGNMENT_NOT_FOUND", "Role assignment not found.", 404)
    if assignment.user_id == permission.auth.user.id and assignment.role.value == "owner_admin":
        raise AppError("LAST_ADMIN_PROTECTION", "An owner cannot revoke their own owner role.", 409)
    assignment.revoked_at = datetime.now(UTC)
    db.commit()
    db.refresh(assignment)
    return assignment_response(assignment)
