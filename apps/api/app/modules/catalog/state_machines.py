from collections.abc import Mapping

from app.core.errors import AppError
from app.modules.catalog.models import InquiryStatus, TrialStatus

INQUIRY_TRANSITIONS: Mapping[InquiryStatus, frozenset[InquiryStatus]] = {
    InquiryStatus.NEW: frozenset({InquiryStatus.CONTACTED, InquiryStatus.CLOSED}),
    InquiryStatus.CONTACTED: frozenset(
        {InquiryStatus.TRIAL_BOOKED, InquiryStatus.CONVERTED, InquiryStatus.CLOSED}
    ),
    InquiryStatus.TRIAL_BOOKED: frozenset({InquiryStatus.CONVERTED, InquiryStatus.CLOSED}),
    InquiryStatus.CONVERTED: frozenset(),
    InquiryStatus.CLOSED: frozenset(),
}

TRIAL_TRANSITIONS: Mapping[TrialStatus, frozenset[TrialStatus]] = {
    TrialStatus.REQUESTED: frozenset({TrialStatus.SCHEDULED, TrialStatus.CANCELLED}),
    TrialStatus.SCHEDULED: frozenset(
        {TrialStatus.ATTENDED, TrialStatus.NO_SHOW, TrialStatus.CANCELLED}
    ),
    TrialStatus.ATTENDED: frozenset(),
    TrialStatus.NO_SHOW: frozenset(),
    TrialStatus.CANCELLED: frozenset(),
}


def require_transition[State: (InquiryStatus, TrialStatus)](
    current: State, target: State, transitions: Mapping[State, frozenset[State]]
) -> None:
    if target not in transitions[current]:
        raise AppError(
            "INVALID_STATE_TRANSITION",
            f"Cannot transition from {current.value} to {target.value}.",
            409,
        )
