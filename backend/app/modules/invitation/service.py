import uuid
import logging
from typing import Sequence
from fastapi import HTTPException, status
from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.models import Invitation, InvitationStatus
from app.modules.invitation.schemas import InvitationCreate, InvitationUpdate
from app.modules.event.service import EventService

logger = logging.getLogger(__name__)

class InvitationService:
    def __init__(self, repo: InvitationRepository, event_service: EventService):
        self.repo = repo
        self.event_service = event_service

    async def _get_owned_invitation_or_404(self, invitation_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> Invitation:
        await self.event_service.get_event_details(event_id, user_id)
        invitation = await self.repo.get_by_id_and_event(invitation_id, event_id)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The invitation does not exist.",
            )
        return invitation

    async def _resolve_and_validate_guests(self, guest_ids: list[uuid.UUID], event_id: uuid.UUID) -> list:
        guests = await self.repo.resolve_guests(guest_ids, event_id)
        if len(guests) != len(guest_ids):
            found_ids = {g.id for g in guests}
            missing = [str(gid) for gid in guest_ids if gid not in found_ids]
            logger.warning("Invalid guest IDs=%s event_id=%s", missing, event_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No guests with the ID: {', '.join(missing)}",
            )
        return guests

    async def create_invitation(self, event_id: uuid.UUID, data: InvitationCreate, user_id: uuid.UUID) -> Invitation:
        await self.event_service.get_event_details(event_id, user_id)

        invitation = Invitation(
            event_id=event_id,
            group_name=data.group_name,
            status=data.status,
        )
        
        self.repo.db.add(invitation)
        await self.repo.db.flush()

        if data.guest_ids:
            guests = await self._resolve_and_validate_guests(data.guest_ids, event_id)
            for guest in guests:
                guest.invitation_id = invitation.id

        await self.repo.db.commit()
        
        return await self.repo.get_by_id_and_event(invitation.id, event_id)

    async def get_invitations_for_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Sequence[Invitation]:
        await self.event_service.get_event_details(event_id, user_id)
        return await self.repo.list_by_event(event_id)

    async def get_invitation_details(self, invitation_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> Invitation:
        return await self._get_owned_invitation_or_404(invitation_id, event_id, user_id)

    async def update_invitation(self, invitation_id: uuid.UUID, event_id: uuid.UUID, data: InvitationUpdate, user_id: uuid.UUID) -> Invitation:
        invitation = await self._get_owned_invitation_or_404(invitation_id, event_id, user_id)

        if data.group_name is not None:
            invitation.group_name = data.group_name
        
        if data.status is not None:
            invitation.status = data.status

        if data.guest_ids is not None:
            for guest in invitation.guests:
                guest.invitation_id = None

            if data.guest_ids:
                guests = await self._resolve_and_validate_guests(data.guest_ids, event_id)
                for guest in guests:
                    guest.invitation_id = invitation.id

        await self.repo.save(invitation)
        logger.info("Updated invitation id=%s", invitation.id)
        
        return await self.repo.get_by_id_and_event(invitation.id, event_id)

    async def update_invitation_status(self, invitation_id: uuid.UUID, event_id: uuid.UUID, new_status: InvitationStatus, user_id: uuid.UUID) -> Invitation:
        invitation = await self._get_owned_invitation_or_404(invitation_id, event_id, user_id)
        invitation.status = new_status
        return await self.repo.save(invitation)

    async def delete_invitation(self, invitation_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        invitation = await self._get_owned_invitation_or_404(invitation_id, event_id, user_id)
        await self.repo.delete(invitation)
        logger.info("Deleted invitation id=%s (guests detached via DB)", invitation_id)