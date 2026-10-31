from app.modules.core.models import Role
from app.modules.core.permissions import role_allows


def test_owner_admin_has_all_core_permissions() -> None:
    assert role_allows(Role.OWNER_ADMIN, "core.audit.view")


def test_guardian_cannot_administer_users() -> None:
    assert not role_allows(Role.GUARDIAN, "core.user.create")


def test_operations_permissions_are_explicit() -> None:
    assert role_allows(Role.OPERATIONS_COORDINATOR, "core.invitation.create")
    assert not role_allows(Role.OPERATIONS_COORDINATOR, "core.audit.view")
