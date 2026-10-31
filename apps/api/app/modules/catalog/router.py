import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import audit
from app.core.authorization import PermissionContext, ScopeService, require_permission
from app.core.database import get_db
from app.core.errors import AppError
from app.modules.catalog.models import Offering, Program, ProgramConfirmation, ProgramStatus, Room
from app.modules.catalog.schemas import (
    ConfirmationUpdate,
    OfferingCreate,
    OfferingResponse,
    ProgramCreate,
    ProgramResponse,
    ProgramUpdate,
    RoomCreate,
    RoomResponse,
)
from app.modules.catalog.service import apply_confirmation, public_offerings_statement
from app.modules.core.models import ScopeType

router = APIRouter(tags=["catalog"])
public_router = APIRouter(tags=["public catalog"])


def program_response(row: Program) -> ProgramResponse:
    return ProgramResponse.model_validate(row, from_attributes=True)


@router.get("/programs", response_model=list[ProgramResponse])
def list_programs(
    _permission: PermissionContext = Depends(require_permission("catalog.program.view")),
    db: Session = Depends(get_db),
) -> list[ProgramResponse]:
    rows = db.scalars(
        select(Program).options(selectinload(Program.confirmation)).order_by(Program.name_sq)
    )
    return [program_response(row) for row in rows]


@router.post("/programs", response_model=ProgramResponse, status_code=201)
def create_program(
    body: ProgramCreate,
    permission: PermissionContext = Depends(require_permission("catalog.program.create")),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    if db.scalar(
        select(Program.id).where((Program.code == body.code) | (Program.slug == body.slug))
    ):
        raise AppError("PROGRAM_DUPLICATE", "Program code or slug already exists.", 409)
    row = Program(
        **body.model_dump(),
        status=ProgramStatus.DRAFT,
        created_at=datetime.now(UTC),
        confirmation=ProgramConfirmation(),
    )
    db.add(row)
    db.flush()
    audit.record(
        db,
        audit.AuditInput(
            action="program.created",
            actor_id=permission.auth.user.id,
            entity_type="program",
            entity_id=row.id,
        ),
    )
    db.commit()
    db.refresh(row)
    return program_response(row)


@router.patch("/programs/{program_id}", response_model=ProgramResponse)
def edit_program(
    program_id: uuid.UUID,
    body: ProgramUpdate,
    permission: PermissionContext = Depends(require_permission("catalog.program.edit")),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    row = db.scalar(
        select(Program).options(selectinload(Program.confirmation)).where(Program.id == program_id)
    )
    if row is None:
        raise AppError("PROGRAM_NOT_FOUND", "Program not found.", 404)
    changes = body.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(row, key, value)
    audit.record(
        db,
        audit.AuditInput(
            action="program.edited",
            actor_id=permission.auth.user.id,
            entity_type="program",
            entity_id=row.id,
            changed_fields=changes,
        ),
    )
    db.commit()
    return program_response(row)


@router.post("/programs/{program_id}/confirm", response_model=ProgramResponse)
def confirm_program(
    program_id: uuid.UUID,
    body: ConfirmationUpdate,
    permission: PermissionContext = Depends(require_permission("catalog.program.view")),
    db: Session = Depends(get_db),
) -> ProgramResponse:
    row = db.scalar(
        select(Program)
        .options(selectinload(Program.confirmation))
        .where(Program.id == program_id)
        .with_for_update()
    )
    if row is None:
        raise AppError("PROGRAM_NOT_FOUND", "Program not found.", 404)
    roles = {assignment.role for assignment in permission.assignments}
    apply_confirmation(
        db, program=row, values=body.model_dump(), roles=roles, actor_id=permission.auth.user.id
    )
    audit.record(
        db,
        audit.AuditInput(
            action="program.confirmed",
            actor_id=permission.auth.user.id,
            entity_type="program",
            entity_id=row.id,
            changed_fields=body.model_dump(exclude_none=True),
        ),
    )
    db.commit()
    return program_response(row)


@router.get("/rooms", response_model=list[RoomResponse])
def list_rooms(
    permission: PermissionContext = Depends(require_permission("catalog.room.view")),
    db: Session = Depends(get_db),
) -> list[RoomResponse]:
    rows = db.scalars(ScopeService.filter(permission, select(Room), Room))
    return [RoomResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/rooms", response_model=RoomResponse, status_code=201)
def create_room(
    body: RoomCreate,
    permission: PermissionContext = Depends(require_permission("catalog.room.create")),
    db: Session = Depends(get_db),
) -> RoomResponse:
    ScopeService.assert_scope_grantable(permission, ScopeType.LOCATION, body.location_id)
    row = Room(**body.model_dump(), created_at=datetime.now(UTC))
    db.add(row)
    db.commit()
    db.refresh(row)
    return RoomResponse.model_validate(row, from_attributes=True)


@router.get("/offerings", response_model=list[OfferingResponse])
def list_offerings(
    permission: PermissionContext = Depends(require_permission("catalog.offering.view")),
    db: Session = Depends(get_db),
) -> list[OfferingResponse]:
    rows = db.scalars(ScopeService.filter(permission, select(Offering), Offering))
    return [OfferingResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/offerings", response_model=OfferingResponse, status_code=201)
def create_offering(
    body: OfferingCreate,
    permission: PermissionContext = Depends(require_permission("catalog.offering.create")),
    db: Session = Depends(get_db),
) -> OfferingResponse:
    ScopeService.assert_scope_grantable(permission, ScopeType.LOCATION, body.location_id)
    if db.scalar(select(Offering.id).where(Offering.slug == body.slug)):
        raise AppError("OFFERING_DUPLICATE", "Offering slug already exists.", 409)
    row = Offering(**body.model_dump(), created_at=datetime.now(UTC))
    db.add(row)
    db.flush()
    audit.record(
        db,
        audit.AuditInput(
            action="offering.created",
            actor_id=permission.auth.user.id,
            entity_type="offering",
            entity_id=row.id,
        ),
    )
    db.commit()
    db.refresh(row)
    return OfferingResponse.model_validate(row, from_attributes=True)


@router.put("/offerings/{offering_id}", response_model=OfferingResponse)
def edit_offering(
    offering_id: uuid.UUID,
    body: OfferingCreate,
    permission: PermissionContext = Depends(require_permission("catalog.offering.edit")),
    db: Session = Depends(get_db),
) -> OfferingResponse:
    row = db.get(Offering, offering_id)
    if row is None:
        raise AppError("OFFERING_NOT_FOUND", "Offering not found.", 404)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    audit.record(
        db,
        audit.AuditInput(
            action="offering.edited",
            actor_id=permission.auth.user.id,
            entity_type="offering",
            entity_id=row.id,
        ),
    )
    db.commit()
    return OfferingResponse.model_validate(row, from_attributes=True)


@public_router.get("/public/offerings", response_model=list[OfferingResponse])
def public_offerings(db: Session = Depends(get_db)) -> list[OfferingResponse]:
    return [
        OfferingResponse.model_validate(row, from_attributes=True)
        for row in db.scalars(public_offerings_statement())
    ]
