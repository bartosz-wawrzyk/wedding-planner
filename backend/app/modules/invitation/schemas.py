import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from app.modules.guest.schemas import GuestResponse

class InvitationStatus(str, Enum):
    NOT_DELIVERED = "NOT_DELIVERED"
    DELIVERED = "DELIVERED"

StrippedStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class InvitationBase(BaseModel):
    group_name: StrippedStr

class InvitationCreate(InvitationBase):
    guest_ids: list[uuid.UUID] = Field(default_factory=list)
    status: InvitationStatus = InvitationStatus.NOT_DELIVERED

class InvitationUpdate(BaseModel):
    group_name: StrippedStr | None = None
    guest_ids: list[uuid.UUID] | None = None
    status: InvitationStatus | None = None

class InvitationStatusUpdate(BaseModel):
    status: InvitationStatus

class InvitationResponse(InvitationBase):
    id: uuid.UUID
    event_id: uuid.UUID
    status: InvitationStatus
    guests: list[GuestResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)