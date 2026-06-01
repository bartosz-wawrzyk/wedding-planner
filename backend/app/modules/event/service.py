import uuid
import logging
from typing import Sequence
from fastapi import HTTPException, status
from app.modules.event.repository import EventRepository
from app.modules.event.models import Event
from app.modules.event.schemas import EventCreate, EventUpdate

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    async def _get_owned_event_or_404(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
        event = await self.repo.get_by_id_and_user(event_id, user_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The event does not exist.",
            )
        return event

    async def create_event(self, data: EventCreate, user_id: uuid.UUID) -> Event:
        event = Event(**data.model_dump(), user_id=user_id)
        created_event = await self.repo.create(event)
        logger.info("Created event id=%s user_id=%s", created_event.id, user_id)
        return created_event

    async def get_events_for_user(self, user_id: uuid.UUID) -> Sequence[Event]:
        return await self.repo.list_by_user(user_id)

    async def get_event_details(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
        return await self._get_owned_event_or_404(event_id, user_id)

    async def update_event(self, event_id: uuid.UUID, data: EventUpdate, user_id: uuid.UUID) -> Event:
        event = await self._get_owned_event_or_404(event_id, user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        updated_event = await self.repo.save(event)
        logger.info("Updated event id=%s", updated_event.id)
        return updated_event

    async def delete_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        event = await self._get_owned_event_or_404(event_id, user_id)
        await self.repo.delete(event)
        logger.info("Deleted event id=%s by user_id=%s", event_id, user_id)