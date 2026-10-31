import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.modules.catalog.models import (
    DeliveryType,
    FeeModel,
    OfferingLanguage,
    OfferingVisibility,
    ProgramCategory,
    ProgramStatus,
)


class ProgramBase(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name_sq: str = Field(min_length=2, max_length=200)
    name_en: str = Field(min_length=2, max_length=200)
    category: ProgramCategory
    description_sq: str | None = None
    description_en: str | None = None
    learning_objectives_sq: str | None = None
    learning_objectives_en: str | None = None
    delivery: DeliveryType
    is_proposed: bool = False


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    name_sq: str | None = None
    name_en: str | None = None
    category: ProgramCategory | None = None
    description_sq: str | None = None
    description_en: str | None = None
    learning_objectives_sq: str | None = None
    learning_objectives_en: str | None = None
    delivery: DeliveryType | None = None


class ConfirmationUpdate(BaseModel):
    eligibility_confirmed: bool | None = None
    duration_confirmed: bool | None = None
    price_confirmed: bool | None = None
    availability_confirmed: bool | None = None


class ConfirmationResponse(BaseModel):
    eligibility_confirmed: bool
    duration_confirmed: bool
    price_confirmed: bool
    availability_confirmed: bool


class ProgramResponse(ProgramBase):
    id: uuid.UUID
    status: ProgramStatus
    confirmed_by: uuid.UUID | None
    confirmed_at: datetime | None
    confirmation: ConfirmationResponse


class RoomCreate(BaseModel):
    location_id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    capacity: int = Field(ge=1, le=500)


class RoomResponse(RoomCreate):
    id: uuid.UUID


class OfferingCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    program_id: uuid.UUID
    location_id: uuid.UUID
    partner_id: uuid.UUID | None = None
    title_sq: str | None = None
    title_en: str | None = None
    language: OfferingLanguage
    age_min: int = Field(ge=0, le=99)
    age_max: int = Field(ge=0, le=99)
    age_reference_date: date
    start_date: date
    end_date: date
    session_minutes: int = Field(ge=15, le=480)
    sessions_planned: int = Field(ge=1, le=500)
    capacity: int = Field(ge=1, le=1000)
    fee_model: FeeModel
    list_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    visibility: OfferingVisibility = OfferingVisibility.DRAFT
    registration_open: bool = False
    waitlist_enabled: bool = False

    @model_validator(mode="after")
    def valid_ranges(self) -> "OfferingCreate":
        if self.age_min > self.age_max:
            raise ValueError("age_min must not exceed age_max")
        if self.start_date > self.end_date:
            raise ValueError("start_date must not exceed end_date")
        if self.fee_model in {FeeModel.FREE, FeeModel.SPONSORED} and self.list_price not in {
            None,
            Decimal("0"),
        }:
            raise ValueError("free or sponsored offerings cannot have a positive list price")
        return self


class OfferingResponse(OfferingCreate):
    id: uuid.UUID
