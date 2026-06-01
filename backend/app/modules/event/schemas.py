import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, field_validator

class EventBase(BaseModel):
    name: str
    date_time: datetime
    ceremony_place: str | None = None
    ceremony_address: str | None = None
    reception_place: str | None = None
    reception_address: str | None = None

    @field_validator("date_time")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        if v < now:
            raise ValueError("The event date cannot be in the past.")
        return v

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: str | None = None
    date_time: datetime | None = None
    ceremony_place: str | None = None
    ceremony_address: str | None = None
    reception_place: str | None = None
    reception_address: str | None = None

    @field_validator("date_time")
    @classmethod
    def validate_future_date(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        if v < now:
            raise ValueError("The event date cannot be in the past.")
        return v

class EventResponse(BaseModel):
    id: uuid.UUID
    name: str
    date_time: datetime
    ceremony_place: str | None = None
    ceremony_address: str | None = None
    reception_place: str | None = None
    reception_address: str | None = None

    model_config = ConfigDict(from_attributes=True)