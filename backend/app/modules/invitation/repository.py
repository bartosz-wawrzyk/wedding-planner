import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.modules.invitation.models import Invitation
from app.modules.guest.models import Guest

class InvitationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_event(self, invitation_id: uuid.UUID, event_id: uuid.UUID) -> Invitation | None:
        result = await self.db.execute(
            select(Invitation)
            .options(selectinload(Invitation.guests))
            .where(
                Invitation.id == invitation_id,
                Invitation.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: uuid.UUID) -> Sequence[Invitation]:
        result = await self.db.execute(
            select(Invitation)
            .options(selectinload(Invitation.guests))
            .where(Invitation.event_id == event_id)
            .order_by(Invitation.group_name)
        )
        return result.scalars().all()

    async def resolve_guests(self, guest_ids: list[uuid.UUID], event_id: uuid.UUID) -> list[Guest]:
        if not guest_ids:
            return []
        
        result = await self.db.execute(
            select(Guest).where(
                Guest.id.in_(guest_ids),
                Guest.event_id == event_id,
            )
        )
        return list(result.scalars().all())

    async def create(self, invitation: Invitation) -> Invitation:
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def save(self, invitation: Invitation) -> Invitation:
        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def delete(self, invitation: Invitation) -> None:
        await self.db.delete(invitation)
        await self.db.commit()