import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.catalog.models import FeeModel, OfferingLanguage
from app.modules.catalog.schemas import OfferingCreate
from app.modules.catalog.service import public_offerings_statement


def offering(**overrides: object) -> OfferingCreate:
    values = {
        "slug": "sample-offering",
        "program_id": uuid.uuid4(),
        "location_id": uuid.uuid4(),
        "language": OfferingLanguage.SQ,
        "age_min": 7,
        "age_max": 10,
        "age_reference_date": date(2026, 9, 1),
        "start_date": date(2026, 9, 1),
        "end_date": date(2026, 12, 15),
        "session_minutes": 75,
        "sessions_planned": 14,
        "capacity": 16,
        "fee_model": FeeModel.PER_CHILD_TERM,
        "list_price": Decimal("120.00"),
    }
    values.update(overrides)
    return OfferingCreate.model_validate(values)


def test_offering_rejects_inverted_age_range() -> None:
    with pytest.raises(ValidationError):
        offering(age_min=12, age_max=8)


def test_free_offering_rejects_positive_price() -> None:
    with pytest.raises(ValidationError):
        offering(fee_model=FeeModel.FREE, list_price=Decimal("1.00"))


def test_public_query_requires_all_publication_guards() -> None:
    sql = str(public_offerings_statement()).lower()
    assert "program.status" in sql
    assert "offering.visibility" in sql
    assert "offering.registration_open" in sql
    assert "program_confirmation.eligibility_confirmed" in sql
    assert "program_confirmation.price_confirmed" in sql
