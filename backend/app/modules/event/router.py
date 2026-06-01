import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.router import get_current_user
from app.modules.event.repository import EventRepository
from app.modules.event.service import EventService
from app.modules.event.schemas import EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])

def get_events_service(db: AsyncSession = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_events_service),
) -> EventResponse:
    event = await event_service.create_event(data, current_user.id)
    return event

@router.get("/", response_model=list[EventResponse])
async def list_events(
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_events_service),
) -> list[EventResponse]:
    return await service.get_events_for_user(current_user.id)

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_events_service),
) -> EventResponse:
    return await service.get_event_details(event_id, current_user.id)

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_events_service),
) -> EventResponse:
    return await service.update_event(event_id, data, current_user.id)

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_events_service),
) -> None:
    await service.delete_event(event_id, current_user.id)