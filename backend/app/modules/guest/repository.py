import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.guest.models import Guest

class GuestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_event(self, guest_id: uuid.UUID, event_id: uuid.UUID) -> Guest | None:
        result = await self.db.execute(
            select(Guest).where(
                Guest.id == guest_id,
                Guest.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: uuid.UUID) -> Sequence[Guest]:
        result = await self.db.execute(
            select(Guest)
            .where(Guest.event_id == event_id)
            .order_by(Guest.full_name)
        )
        return result.scalars().all()

    async def create(self, guest: Guest) -> Guest:
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def save(self, guest: Guest) -> Guest:
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def delete(self, guest: Guest) -> None:
        await self.db.delete(guest)
        await self.db.commit()