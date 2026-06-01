import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.modules.guest.models import GuestType, GuestSide, ConfirmationStatus

class GuestBase(BaseModel):
    full_name: str
    guest_type: GuestType = GuestType.ADULT
    side: GuestSide
    confirmation_status: ConfirmationStatus = ConfirmationStatus.PENDING
    has_accommodation: bool = False
    has_day_after: bool = False
    dietary_requirements: str | None = None
    contact_info: str | None = None
    position_index: int | None = Field(default=None, ge=1)

    @field_validator("full_name")
    @classmethod
    def trim_and_validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("The guest's first and last name cannot be left blank")
        return trimmed

class GuestCreate(GuestBase):
    invitation_id: uuid.UUID | None = None

class GuestUpdate(BaseModel):
    full_name: str | None = None
    guest_type: GuestType | None = None
    side: GuestSide | None = None
    confirmation_status: ConfirmationStatus | None = None
    has_accommodation: bool | None = None
    has_day_after: bool | None = None
    dietary_requirements: str | None = None
    contact_info: str | None = None
    invitation_id: uuid.UUID | None = None
    position_index: int | None = Field(default=None, ge=1)

    @field_validator("full_name")
    @classmethod
    def trim_and_validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("The guest's first and last name cannot be left blank")
        return trimmed

class GuestResponse(GuestBase):
    id: uuid.UUID
    invitation_id: uuid.UUID | None
    table_id: uuid.UUID | None
    confirmation_status: ConfirmationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)