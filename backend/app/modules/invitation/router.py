import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.router import get_current_user
from app.modules.event.repository import EventRepository
from app.modules.event.service import EventService
from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.service import InvitationService
from app.modules.invitation.schemas import (
    InvitationCreate, 
    InvitationUpdate, 
    InvitationResponse, 
    InvitationStatus, 
    InvitationStatusUpdate
)

router = APIRouter(prefix="/events/{event_id}/invitations", tags=["invitations"])

def get_invitation_service(db: AsyncSession = Depends(get_db)) -> InvitationService:
    event_repo = EventRepository(db)
    event_service = EventService(event_repo)
    invitation_repo = InvitationRepository(db)
    return InvitationService(invitation_repo, event_service)

@router.post("/", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    event_id: uuid.UUID,
    data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationResponse:
    return await service.create_invitation(event_id, data, current_user.id)

@router.get("/", response_model=list[InvitationResponse])
async def list_invitations(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> list[InvitationResponse]:
    return await service.get_invitations_for_event(event_id, current_user.id)

@router.get("/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(
    event_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationResponse:
    return await service.get_invitation_details(invitation_id, event_id, current_user.id)

@router.patch("/{invitation_id}", response_model=InvitationResponse)
async def update_invitation(
    event_id: uuid.UUID,
    invitation_id: uuid.UUID,
    data: InvitationUpdate,
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationResponse:
    return await service.update_invitation(invitation_id, event_id, data, current_user.id)

@router.patch("/{invitation_id}/status", response_model=InvitationResponse)
async def update_invitation_status(
    event_id: uuid.UUID,
    invitation_id: uuid.UUID,
    payload: InvitationStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationResponse:
    return await service.update_invitation_status(invitation_id, event_id, payload.status, current_user.id)

@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    event_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> None:
    await service.delete_invitation(invitation_id, event_id, current_user.id)