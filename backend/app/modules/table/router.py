import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.router import get_current_user
from app.modules.event.repository import EventRepository
from app.modules.event.service import EventService
from app.modules.table.repository import TableRepository
from app.modules.table.service import TableService
from app.modules.table.schemas import TableCreate, TableUpdate, TableResponse, GuestSeatAssignment
from app.modules.guest.schemas import GuestResponse

router = APIRouter(prefix="/events/{event_id}/tables", tags=["tables"])

def get_table_service(db: AsyncSession = Depends(get_db)) -> TableService:
    event_repo = EventRepository(db)
    event_service = EventService(event_repo)
    table_repo = TableRepository(db)
    return TableService(table_repo, event_service)

@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    event_id: uuid.UUID,
    data: TableCreate,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> TableResponse:
    return await service.create_table(event_id, data, current_user.id)

@router.get("/", response_model=list[TableResponse])
async def list_tables(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> list[TableResponse]:
    return await service.get_tables_for_event(event_id, current_user.id)

@router.get("/guests/unassigned", response_model=list[GuestResponse])
async def list_unassigned_guests(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> list[GuestResponse]:
    return await service.get_unassigned_guests(event_id, current_user.id)

@router.get("/{table_id}", response_model=TableResponse)
async def get_table(
    event_id: uuid.UUID,
    table_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> TableResponse:
    return await service.get_table_details(table_id, event_id, current_user.id)

@router.patch("/{table_id}", response_model=TableResponse)
async def update_table(
    event_id: uuid.UUID,
    table_id: uuid.UUID,
    data: TableUpdate,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> TableResponse:
    return await service.update_table(table_id, event_id, data, current_user.id)

@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
    event_id: uuid.UUID,
    table_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> None:
    await service.delete_table(table_id, event_id, current_user.id)

@router.get("/{table_id}/guests", response_model=list[GuestResponse])
async def get_table_guests(
    event_id: uuid.UUID,
    table_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> list[GuestResponse]:
    return await service.get_table_guests(table_id, event_id, current_user.id)

@router.delete("/{table_id}/guests/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_guest_from_table(
    event_id: uuid.UUID,
    table_id: uuid.UUID,
    guest_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> None:
    await service.unassign_guest(table_id, guest_id, event_id, current_user.id)

@router.put("/{table_id}/seating", response_model=TableResponse)
async def update_table_seating(
    event_id: uuid.UUID,
    table_id: uuid.UUID,
    assignments: list[GuestSeatAssignment],
    current_user: User = Depends(get_current_user),
    service: TableService = Depends(get_table_service),
) -> TableResponse:
    return await service.update_seating(table_id, event_id, assignments, current_user.id)