import uuid
import logging
from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy import select
from app.modules.guest.repository import GuestRepository
from app.modules.guest.models import Guest
from app.modules.guest.schemas import GuestCreate, GuestUpdate
from app.modules.event.service import EventService
from app.modules.invitation.models import Invitation

logger = logging.getLogger(__name__)

class GuestService:
    def __init__(self, repo: GuestRepository, event_service: EventService):
        self.repo = repo
        self.event_service = event_service

    async def _validate_invitation(self, invitation_id: uuid.UUID, event_id: uuid.UUID) -> None:
        result = await self.repo.db.execute(
            select(Invitation).where(
                Invitation.id == invitation_id,
                Invitation.event_id == event_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The invitation does not exist or is not associated with this event.",
            )

    async def create_guest(self, event_id: uuid.UUID, data: GuestCreate, user_id: uuid.UUID) -> Guest:
        await self.event_service.get_event_details(event_id, user_id)

        if data.invitation_id:
            await self._validate_invitation(data.invitation_id, event_id)

        guest = Guest(**data.model_dump(), event_id=event_id)
        created_guest = await self.repo.create(guest)
        logger.info("Created guest id=%s event_id=%s", created_guest.id, event_id)
        return created_guest

    async def get_guests_for_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Sequence[Guest]:
        await self.event_service.get_event_details(event_id, user_id)
        return await self.repo.list_by_event(event_id)

    async def get_guest_details(self, guest_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> Guest:
        await self.event_service.get_event_details(event_id, user_id)
        guest = await self.repo.get_by_id_and_event(guest_id, event_id)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The guest does not exist.",
            )
        return guest

    async def update_guest(self, guest_id: uuid.UUID, event_id: uuid.UUID, data: GuestUpdate, user_id: uuid.UUID) -> Guest:
        guest = await self.get_guest_details(guest_id, event_id, user_id)
        update_data = data.model_dump(exclude_unset=True)

        if "invitation_id" in update_data and update_data["invitation_id"] is not None:
            await self._validate_invitation(update_data["invitation_id"], event_id)

        for field, value in update_data.items():
            setattr(guest, field, value)

        updated_guest = await self.repo.save(guest)
        logger.info("Updated guest id=%s", updated_guest.id)
        return updated_guest

    async def delete_guest(self, guest_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        guest = await self.get_guest_details(guest_id, event_id, user_id)
        await self.repo.delete(guest)
        logger.info("Deleted guest id=%s event_id=%s", guest_id, event_id)