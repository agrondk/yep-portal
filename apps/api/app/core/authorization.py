import uuid
from collections.abc import Callable
from datetime import date
from typing import Any, ClassVar, Protocol, TypeVar

from fastapi import Depends
from sqlalchemy import Select, false, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.modules.core.auth_dependencies import AuthContext, current_auth
from app.modules.core.models import Role, RoleAssignment, ScopeType
from app.modules.core.permissions import role_allows


class ScopedRecord(Protocol):
    id: uuid.UUID


T = TypeVar("T", bound=ScopedRecord)


def current_assignments(db: Session, user_id: uuid.UUID) -> list[RoleAssignment]:
    today = date.today()
    return list(
        db.scalars(
            select(RoleAssignment).where(
                RoleAssignment.user_id == user_id,
                RoleAssignment.revoked_at.is_(None),
                RoleAssignment.valid_from <= today,
                or_(RoleAssignment.valid_to.is_(None), RoleAssignment.valid_to >= today),
            )
        )
    )


class PermissionContext:
    def __init__(self, auth: AuthContext, assignments: list[RoleAssignment]) -> None:
        self.auth = auth
        self.assignments = assignments


def require_permission(permission: str) -> Callable[..., PermissionContext]:
    def dependency(
        auth: AuthContext = Depends(current_auth), db: Session = Depends(get_db)
    ) -> PermissionContext:
        assignments = current_assignments(db, auth.user.id)
        if not any(role_allows(assignment.role, permission) for assignment in assignments):
            raise AppError("PERMISSION_DENIED", "You do not have permission for this action.", 403)
        return PermissionContext(auth, assignments)

    return dependency


class ScopeService:
    COLUMN_BY_SCOPE: ClassVar[dict[ScopeType, str]] = {
        ScopeType.ORGANIZATION: "organization_id",
        ScopeType.LOCATION: "location_id",
        ScopeType.PARTNER: "partner_id",
        ScopeType.PROGRAM: "program_id",
        ScopeType.COHORT: "cohort_id",
        ScopeType.INITIATIVE: "initiative_id",
        ScopeType.HOUSEHOLD: "household_id",
    }

    @classmethod
    def filter(
        cls, context: PermissionContext, statement: Select[Any], entity: type[T]
    ) -> Select[Any]:
        if any(
            assignment.role is Role.OWNER_ADMIN
            and assignment.scope_type is ScopeType.ORGANIZATION
            and assignment.scope_id is None
            for assignment in context.assignments
        ):
            return statement
        clauses = []
        for assignment in context.assignments:
            column_name = cls.COLUMN_BY_SCOPE[assignment.scope_type]
            column = getattr(entity, column_name, None)
            if assignment.scope_id is not None and column is not None:
                clauses.append(column == assignment.scope_id)
        return statement.where(or_(*clauses) if clauses else false())

    @classmethod
    def assert_can(cls, context: PermissionContext, record: ScopedRecord) -> None:
        if any(
            assignment.role is Role.OWNER_ADMIN
            and assignment.scope_type is ScopeType.ORGANIZATION
            and assignment.scope_id is None
            for assignment in context.assignments
        ):
            return
        for assignment in context.assignments:
            column_name = cls.COLUMN_BY_SCOPE[assignment.scope_type]
            if (
                assignment.scope_id is not None
                and getattr(record, column_name, None) == assignment.scope_id
            ):
                return
        raise AppError("SCOPE_DENIED", "This record is outside your assigned scope.", 403)

    @staticmethod
    def can_manage_scope(
        context: PermissionContext, scope_type: ScopeType, scope_id: uuid.UUID | None
    ) -> bool:
        for assignment in context.assignments:
            if (
                assignment.role is Role.OWNER_ADMIN
                and assignment.scope_type is ScopeType.ORGANIZATION
                and assignment.scope_id is None
            ):
                return True
            if assignment.scope_type is scope_type and assignment.scope_id == scope_id:
                return True
        return False

    @classmethod
    def assert_scope_grantable(
        cls, context: PermissionContext, scope_type: ScopeType, scope_id: uuid.UUID | None
    ) -> None:
        if not cls.can_manage_scope(context, scope_type, scope_id):
            raise AppError("SCOPE_DENIED", "You cannot grant access to this scope.", 403)
