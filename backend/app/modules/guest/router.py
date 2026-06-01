import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.router import get_current_user
from app.modules.event.repository import EventRepository
from app.modules.event.service import EventService
from app.modules.guest.repository import GuestRepository
from app.modules.guest.service import GuestService
from app.modules.guest.schemas import GuestCreate, GuestUpdate, GuestResponse

router = APIRouter(prefix="/events/{event_id}/guests", tags=["guests"])

def get_guest_service(db: AsyncSession = Depends(get_db)) -> GuestService:
    event_repo = EventRepository(db)
    event_service = EventService(event_repo)
    guest_repo = GuestRepository(db)
    return GuestService(guest_repo, event_service)

@router.post("/", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
async def create_guest(
    event_id: uuid.UUID,
    data: GuestCreate,
    current_user: User = Depends(get_current_user),
    service: GuestService = Depends(get_guest_service),
) -> GuestResponse:
    return await service.create_guest(event_id, data, current_user.id)

@router.get("/", response_model=list[GuestResponse])
async def list_guests(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GuestService = Depends(get_guest_service),
) -> list[GuestResponse]:
    return await service.get_guests_for_event(event_id, current_user.id)

@router.get("/{guest_id}", response_model=GuestResponse)
async def get_guest(
    event_id: uuid.UUID,
    guest_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GuestService = Depends(get_guest_service),
) -> GuestResponse:
    return await service.get_guest_details(guest_id, event_id, current_user.id)

@router.patch("/{guest_id}", response_model=GuestResponse)
async def update_guest(
    event_id: uuid.UUID,
    guest_id: uuid.UUID,
    data: GuestUpdate,
    current_user: User = Depends(get_current_user),
    service: GuestService = Depends(get_guest_service),
) -> GuestResponse:
    return await service.update_guest(guest_id, event_id, data, current_user.id)

@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guest(
    event_id: uuid.UUID,
    guest_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: GuestService = Depends(get_guest_service),
) -> None:
    await service.delete_guest(guest_id, event_id, current_user.id)