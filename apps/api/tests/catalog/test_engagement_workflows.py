import pytest
from pydantic import ValidationError

from app.core.errors import AppError
from app.modules.catalog.models import InquiryStatus, TrialStatus
from app.modules.catalog.schemas import InquiryTransition
from app.modules.catalog.state_machines import (
    INQUIRY_TRANSITIONS,
    TRIAL_TRANSITIONS,
    require_transition,
)
from app.modules.core.models import Role
from app.modules.core.permissions import role_allows


def test_inquiry_conversion_journey_is_allowed() -> None:
    require_transition(InquiryStatus.NEW, InquiryStatus.CONTACTED, INQUIRY_TRANSITIONS)
    require_transition(InquiryStatus.CONTACTED, InquiryStatus.TRIAL_BOOKED, INQUIRY_TRANSITIONS)
    require_transition(InquiryStatus.TRIAL_BOOKED, InquiryStatus.CONVERTED, INQUIRY_TRANSITIONS)


def test_trial_attendance_journey_is_allowed() -> None:
    require_transition(TrialStatus.REQUESTED, TrialStatus.SCHEDULED, TRIAL_TRANSITIONS)
    require_transition(TrialStatus.SCHEDULED, TrialStatus.ATTENDED, TRIAL_TRANSITIONS)


def test_terminal_state_cannot_be_reopened() -> None:
    with pytest.raises(AppError) as caught:
        require_transition(InquiryStatus.CLOSED, InquiryStatus.CONTACTED, INQUIRY_TRANSITIONS)
    assert caught.value.code == "INVALID_STATE_TRANSITION"
    assert caught.value.status_code == 409


def test_closing_inquiry_requires_reason() -> None:
    with pytest.raises(ValidationError):
        InquiryTransition(status=InquiryStatus.CLOSED)


def test_coordinator_has_engagement_permissions() -> None:
    assert role_allows(Role.OPERATIONS_COORDINATOR, "catalog.inquiry.assign")
    assert role_allows(Role.OPERATIONS_COORDINATOR, "catalog.inquiry.transition")
    assert role_allows(Role.OPERATIONS_COORDINATOR, "catalog.trial.schedule")
    assert role_allows(Role.OPERATIONS_COORDINATOR, "catalog.trial.transition")


def test_public_only_role_has_no_staff_engagement_permissions() -> None:
    assert not role_allows(Role.GUARDIAN, "catalog.inquiry.view")
    assert not role_allows(Role.GUARDIAN, "catalog.trial.view")
