from app.modules.catalog.permissions import CATALOG_PERMISSIONS
from app.modules.core.models import Role

CORE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.OWNER_ADMIN: frozenset({"core.*"}),
    Role.OPERATIONS_COORDINATOR: frozenset(
        {
            "core.user.view",
            "core.user.create",
            "core.user.edit",
            "core.invitation.view",
            "core.invitation.create",
            "core.location.view",
            "core.location.create",
            "core.location.edit",
            "core.job.view",
            "core.file.create",
            "core.file.view",
        }
    ),
    Role.FINANCE_OFFICER: frozenset(
        {"core.user.view", "core.job.view", "core.file.create", "core.file.view"}
    ),
    Role.INSTRUCTOR: frozenset({"core.file.create", "core.file.view"}),
    Role.MARKETING_COORDINATOR: frozenset(),
    Role.GUARDIAN: frozenset({"core.file.create", "core.file.view"}),
    Role.STUDENT: frozenset(),
    Role.SCHOOL_COORDINATOR: frozenset(),
    Role.SPONSOR: frozenset(),
}


def role_allows(role: Role, permission: str) -> bool:
    allowed = CORE_PERMISSIONS.get(role, frozenset()) | CATALOG_PERMISSIONS.get(role, frozenset())
    module = permission.split(".", 1)[0]
    return permission in allowed or f"{module}.*" in allowed
