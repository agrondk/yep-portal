import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.authorization import PermissionContext, require_permission
from app.core.database import get_db
from app.core.errors import AppError
from app.core.rate_limit import rate_limiter
from app.modules.catalog.models import (
    Inquiry,
    InquiryStatus,
    Offering,
    Program,
    TrialBooking,
    TrialStatus,
)
from app.modules.catalog.schemas import (
    InquiryAssign,
    InquiryCreate,
    InquiryResponse,
    InquiryTransition,
    TrialBookingResponse,
    TrialRequestCreate,
    TrialSchedule,
    TrialTransition,
)
from app.modules.catalog.service import public_offerings_statement
from app.modules.catalog.state_machines import (
    INQUIRY_TRANSITIONS,
    TRIAL_TRANSITIONS,
    require_transition,
)
from app.modules.core.models import User

router = APIRouter(tags=["catalog engagement"])
public_router = APIRouter(tags=["public catalog"])


def _visitor_key(request: Request, action: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"catalog:{action}:{host}"


def _reject_honeypot(value: str) -> None:
    if value:
        raise AppError("SUBMISSION_REJECTED", "Submission could not be accepted.", 400)


def _new_inquiry(body: InquiryCreate) -> Inquiry:
    values = body.model_dump(exclude={"website"})
    return Inquiry(**values, status=InquiryStatus.NEW, created_at=datetime.now(UTC))


@public_router.post("/public/inquiries", response_model=InquiryResponse, status_code=201)
def create_public_inquiry(
    body: InquiryCreate, request: Request, db: Session = Depends(get_db)
) -> InquiryResponse:
    rate_limiter.check(_visitor_key(request, "inquiry"), limit=5, window_seconds=3600)
    _reject_honeypot(body.website)
    if body.program_id is not None and db.get(Program, body.program_id) is None:
        raise AppError("PROGRAM_NOT_FOUND", "Program not found.", 404)
    row = _new_inquiry(body)
    db.add(row)
    db.flush()
    audit.record(
        db,
        audit.AuditInput(
            action="inquiry.received",
            actor_type="visitor",
            entity_type="inquiry",
            entity_id=row.id,
        ),
    )
    db.commit()
    db.refresh(row)
    return InquiryResponse.model_validate(row, from_attributes=True)


@public_router.post("/public/trial-requests", response_model=TrialBookingResponse, status_code=201)
def create_public_trial_request(
    body: TrialRequestCreate, request: Request, db: Session = Depends(get_db)
) -> TrialBookingResponse:
    rate_limiter.check(_visitor_key(request, "trial"), limit=5, window_seconds=3600)
    _reject_honeypot(body.website)
    offering = db.scalar(public_offerings_statement().where(Offering.id == body.offering_id))
    if offering is None:
        raise AppError("OFFERING_NOT_AVAILABLE", "Offering is not available for trials.", 404)
    inquiry_data = body.model_dump()
    inquiry_data["program_id"] = offering.program_id
    inquiry = _new_inquiry(InquiryCreate.model_validate(inquiry_data))
    db.add(inquiry)
    db.flush()
    trial = TrialBooking(
        inquiry_id=inquiry.id,
        offering_id=offering.id,
        date_time=body.date_time,
        status=TrialStatus.REQUESTED,
        created_at=datetime.now(UTC),
    )
    db.add(trial)
    db.flush()
    audit.record(
        db,
        audit.AuditInput(
            action="inquiry.received",
            actor_type="visitor",
            entity_type="inquiry",
            entity_id=inquiry.id,
            subject_refs={"trial_booking_id": str(trial.id)},
        ),
    )
    db.commit()
    db.refresh(trial)
    return TrialBookingResponse.model_validate(trial, from_attributes=True)


@router.get("/inquiries", response_model=list[InquiryResponse])
def list_inquiries(
    _permission: PermissionContext = Depends(require_permission("catalog.inquiry.view")),
    db: Session = Depends(get_db),
) -> list[InquiryResponse]:
    rows = db.scalars(select(Inquiry).order_by(Inquiry.created_at.desc()))
    return [InquiryResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/inquiries/{inquiry_id}/assign", response_model=InquiryResponse)
def assign_inquiry(
    inquiry_id: uuid.UUID,
    body: InquiryAssign,
    permission: PermissionContext = Depends(require_permission("catalog.inquiry.assign")),
    db: Session = Depends(get_db),
) -> InquiryResponse:
    row = db.get(Inquiry, inquiry_id)
    if row is None:
        raise AppError("INQUIRY_NOT_FOUND", "Inquiry not found.", 404)
    if db.get(User, body.assigned_to) is None:
        raise AppError("USER_NOT_FOUND", "Assigned user not found.", 404)
    row.assigned_to = body.assigned_to
    audit.record(
        db,
        audit.AuditInput(
            action="inquiry.assigned",
            actor_id=permission.auth.user.id,
            entity_type="inquiry",
            entity_id=row.id,
            changed_fields={"assigned_to": str(body.assigned_to)},
        ),
    )
    db.commit()
    return InquiryResponse.model_validate(row, from_attributes=True)


@router.post("/inquiries/{inquiry_id}/transition", response_model=InquiryResponse)
def transition_inquiry(
    inquiry_id: uuid.UUID,
    body: InquiryTransition,
    permission: PermissionContext = Depends(require_permission("catalog.inquiry.transition")),
    db: Session = Depends(get_db),
) -> InquiryResponse:
    row = db.get(Inquiry, inquiry_id, with_for_update=True)
    if row is None:
        raise AppError("INQUIRY_NOT_FOUND", "Inquiry not found.", 404)
    previous = row.status
    require_transition(previous, body.status, INQUIRY_TRANSITIONS)
    row.status = body.status
    row.closed_reason = body.closed_reason if body.status is InquiryStatus.CLOSED else None
    audit.record(
        db,
        audit.AuditInput(
            action="inquiry.transitioned",
            actor_id=permission.auth.user.id,
            entity_type="inquiry",
            entity_id=row.id,
            changed_fields={"status": {"from": previous.value, "to": body.status.value}},
        ),
    )
    db.commit()
    return InquiryResponse.model_validate(row, from_attributes=True)


@router.get("/trial-bookings", response_model=list[TrialBookingResponse])
def list_trial_bookings(
    _permission: PermissionContext = Depends(require_permission("catalog.trial.view")),
    db: Session = Depends(get_db),
) -> list[TrialBookingResponse]:
    rows = db.scalars(select(TrialBooking).order_by(TrialBooking.date_time))
    return [TrialBookingResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/trial-bookings/{trial_id}/schedule", response_model=TrialBookingResponse)
def schedule_trial(
    trial_id: uuid.UUID,
    body: TrialSchedule,
    permission: PermissionContext = Depends(require_permission("catalog.trial.schedule")),
    db: Session = Depends(get_db),
) -> TrialBookingResponse:
    row = db.get(TrialBooking, trial_id, with_for_update=True)
    if row is None:
        raise AppError("TRIAL_NOT_FOUND", "Trial booking not found.", 404)
    require_transition(row.status, TrialStatus.SCHEDULED, TRIAL_TRANSITIONS)
    inquiry = db.get(Inquiry, row.inquiry_id, with_for_update=True)
    if inquiry is None:
        raise AppError("INQUIRY_NOT_FOUND", "Inquiry not found.", 404)
    require_transition(inquiry.status, InquiryStatus.TRIAL_BOOKED, INQUIRY_TRANSITIONS)
    previous_date = row.date_time
    row.date_time = body.date_time
    row.status = TrialStatus.SCHEDULED
    inquiry.status = InquiryStatus.TRIAL_BOOKED
    audit.record(
        db,
        audit.AuditInput(
            action="trial.scheduled",
            actor_id=permission.auth.user.id,
            entity_type="trial_booking",
            entity_id=row.id,
            changed_fields={
                "date_time": {"from": previous_date.isoformat(), "to": body.date_time.isoformat()}
            },
        ),
    )
    audit.record(
        db,
        audit.AuditInput(
            action="inquiry.transitioned",
            actor_id=permission.auth.user.id,
            entity_type="inquiry",
            entity_id=inquiry.id,
            changed_fields={
                "status": {
                    "from": InquiryStatus.CONTACTED.value,
                    "to": InquiryStatus.TRIAL_BOOKED.value,
                }
            },
        ),
    )
    db.commit()
    return TrialBookingResponse.model_validate(row, from_attributes=True)


@router.post("/trial-bookings/{trial_id}/transition", response_model=TrialBookingResponse)
def transition_trial(
    trial_id: uuid.UUID,
    body: TrialTransition,
    permission: PermissionContext = Depends(require_permission("catalog.trial.transition")),
    db: Session = Depends(get_db),
) -> TrialBookingResponse:
    row = db.get(TrialBooking, trial_id, with_for_update=True)
    if row is None:
        raise AppError("TRIAL_NOT_FOUND", "Trial booking not found.", 404)
    previous = row.status
    require_transition(previous, body.status, TRIAL_TRANSITIONS)
    row.status = body.status
    row.outcome_note = body.outcome_note
    audit.record(
        db,
        audit.AuditInput(
            action="trial.transitioned",
            actor_id=permission.auth.user.id,
            entity_type="trial_booking",
            entity_id=row.id,
            changed_fields={"status": {"from": previous.value, "to": body.status.value}},
        ),
    )
    db.commit()
    return TrialBookingResponse.model_validate(row, from_attributes=True)
