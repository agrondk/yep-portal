from app.modules.core.models import Role

CATALOG_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.OWNER_ADMIN: frozenset({"catalog.*"}),
    Role.OPERATIONS_COORDINATOR: frozenset(
        {
            "catalog.program.view",
            "catalog.program.create",
            "catalog.program.edit",
            "catalog.program.confirm",
            "catalog.offering.view",
            "catalog.offering.create",
            "catalog.offering.edit",
            "catalog.room.view",
            "catalog.room.create",
            "catalog.room.edit",
        }
    ),
    Role.FINANCE_OFFICER: frozenset(
        {"catalog.program.view", "catalog.program.confirm_price", "catalog.offering.view"}
    ),
}
