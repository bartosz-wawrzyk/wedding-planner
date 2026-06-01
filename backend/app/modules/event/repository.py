import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.event.models import Event

class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_user(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Event | None:
        result = await self.db.execute(
            select(Event).where(
                Event.id == event_id,
                Event.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Event]:
        result = await self.db.execute(
            select(Event)
            .where(Event.user_id == user_id)
            .order_by(Event.date_time)
        )
        return result.scalars().all()

    async def create(self, event: Event) -> Event:
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def save(self, event: Event) -> Event:
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def delete(self, event: Event) -> None:
        await self.db.delete(event)
        await self.db.commit()