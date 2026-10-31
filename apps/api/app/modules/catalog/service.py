import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.modules.catalog.models import (
    Offering,
    OfferingVisibility,
    Program,
    ProgramConfirmation,
    ProgramStatus,
)
from app.modules.core.models import Role


def public_offerings_statement() -> Select[Offering]:
    return (
        select(Offering)
        .options(selectinload(Offering.program))
        .join(Program, Offering.program_id == Program.id)
        .join(ProgramConfirmation, ProgramConfirmation.program_id == Program.id)
        .where(
            and_(
                Program.status == ProgramStatus.CONFIRMED,
                Offering.visibility == OfferingVisibility.PUBLISHED,
                Offering.registration_open.is_(True),
                ProgramConfirmation.eligibility_confirmed.is_(True),
                ProgramConfirmation.price_confirmed.is_(True),
            )
        )
    )


def apply_confirmation(
    db: Session,
    *,
    program: Program,
    values: dict[str, bool | None],
    roles: set[Role],
    actor_id: uuid.UUID,
) -> Program:
    price = values.get("price_confirmed")
    non_price = any(
        values.get(key) is not None
        for key in ("eligibility_confirmed", "duration_confirmed", "availability_confirmed")
    )
    if price is not None and not roles.intersection({Role.OWNER_ADMIN, Role.FINANCE_OFFICER}):
        raise AppError(
            "PRICE_CONFIRMATION_DENIED", "Only finance or the owner may confirm price.", 403
        )
    if non_price and not roles.intersection({Role.OWNER_ADMIN, Role.OPERATIONS_COORDINATOR}):
        raise AppError(
            "PROGRAM_CONFIRMATION_DENIED", "You cannot confirm these program fields.", 403
        )
    confirmation = program.confirmation
    for key, value in values.items():
        if value is not None:
            setattr(confirmation, key, value)
    if all(
        (
            confirmation.eligibility_confirmed,
            confirmation.duration_confirmed,
            confirmation.price_confirmed,
            confirmation.availability_confirmed,
        )
    ):
        program.status = ProgramStatus.CONFIRMED
        program.confirmed_by = actor_id
        program.confirmed_at = datetime.now(UTC)
    else:
        program.status = ProgramStatus.DRAFT
        program.confirmed_by = None
        program.confirmed_at = None
    return program
