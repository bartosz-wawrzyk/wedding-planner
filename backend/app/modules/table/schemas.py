import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.modules.table.models import TableShape

class TableBase(BaseModel):
    number: int = Field(gt=0)
    name: str | None = None
    shape: TableShape = TableShape.ROUND
    capacity: int = Field(gt=0)

class TableCreate(TableBase):
    pass

class TableUpdate(BaseModel):
    number: int | None = Field(default=None, gt=0)
    name: str | None = None
    shape: TableShape | None = None
    capacity: int | None = Field(default=None, gt=0)

class GuestSeatAssignment(BaseModel):
    guest_id: uuid.UUID
    position_index: int = Field(ge=1)

class TableResponse(TableBase):
    id: uuid.UUID
    event_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)