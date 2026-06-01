import uuid
import logging
from typing import Sequence
from fastapi import HTTPException, status
from app.modules.table.repository import TableRepository
from app.modules.table.models import Table
from app.modules.guest.models import Guest
from app.modules.table.schemas import TableCreate, TableUpdate, GuestSeatAssignment
from app.modules.event.service import EventService

logger = logging.getLogger(__name__)

class TableService:
    def __init__(self, repo: TableRepository, event_service: EventService):
        self.repo = repo
        self.event_service = event_service

    async def _get_owned_table_or_404(self, table_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> Table:
        await self.event_service.get_event_details(event_id, user_id)
        table = await self.repo.get_by_id_and_event(table_id, event_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The table doesn't exist")
        return table

    async def create_table(self, event_id: uuid.UUID, data: TableCreate, user_id: uuid.UUID) -> Table:
        await self.event_service.get_event_details(event_id, user_id)
        table = Table(**data.model_dump(), event_id=event_id)
        try:
            return await self.repo.create(table)
        except Exception:
            logger.exception("create_table failed")
            raise HTTPException(status_code=500, detail="The table could not be created.")

    async def get_tables_for_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Sequence[Table]:
        await self.event_service.get_event_details(event_id, user_id)
        return await self.repo.list_by_event(event_id)

    async def get_table_details(self, table_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> Table:
        return await self._get_owned_table_or_404(table_id, event_id, user_id)

    async def update_table(self, table_id: uuid.UUID, event_id: uuid.UUID, data: TableUpdate, user_id: uuid.UUID) -> Table:
        table = await self._get_owned_table_or_404(table_id, event_id, user_id)
        
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(table, k, v)
            
        try:
            return await self.repo.save(table)
        except Exception:
            logger.exception("update_table failed")
            raise HTTPException(status_code=500, detail="The table could not be updated.")

    async def delete_table(self, table_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        table = await self._get_owned_table_or_404(table_id, event_id, user_id)
        
        for guest in table.guests:
            guest.table_id = None
            guest.position_index = None
            
        await self.repo.repo.db.flush() if hasattr(self.repo, 'repo') else await self.repo.db.flush()
        
        try:
            await self.repo.delete(table)
        except Exception:
            logger.exception("delete_table failed")
            raise HTTPException(status_code=500, detail="The table could not be deleted.")

    async def get_table_guests(self, table_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> list[Guest]:
        table = await self._get_owned_table_or_404(table_id, event_id, user_id)
        return table.guests

    async def unassign_guest(self, table_id: uuid.UUID, guest_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.event_service.get_event_details(event_id, user_id)
        guest = await self.repo.get_guest_assigned_to_table(guest_id, table_id, event_id)
        if not guest:
            raise HTTPException(status_code=404, detail="The guest could not be found.")
            
        guest.table_id = None
        guest.position_index = None
        
        try:
            await self.repo.save(guest)
        except Exception:
            logger.exception("unassign_guest failed")
            raise HTTPException(status_code=500, detail="The guest could not be unassigned from the table")

    async def update_seating(self, table_id: uuid.UUID, event_id: uuid.UUID, assignments: list[GuestSeatAssignment], user_id: uuid.UUID) -> Table:
        table = await self._get_owned_table_or_404(table_id, event_id, user_id)

        if len(assignments) > table.capacity:
            raise HTTPException(status_code=400, detail=f"The table has a capacity of {table.capacity}")

        positions = [a.position_index for a in assignments]
        if len(set(positions)) != len(positions):
            raise HTTPException(status_code=400, detail="Duplicate positions")
            
        guest_ids = [a.guest_id for a in assignments]
        if len(set(guest_ids)) != len(guest_ids):
            raise HTTPException(status_code=400, detail="Duplicate guests")

        guests = await self.repo.get_guests_by_ids_and_event(guest_ids, event_id)
        if len(guests) != len(guest_ids):
            raise HTTPException(status_code=400, detail="Some guests could not be found")

        guest_map = {g.id: g for g in guests}
        for g in guests:
            g.table_id = None
            g.position_index = None
        await self.repo.db.flush()

        for assignment in assignments:
            g = guest_map[assignment.guest_id]
            g.table_id = table.id
            g.position_index = assignment.position_index

        try:
            await self.repo.save(table)
            return await self.repo.get_by_id_and_event(table.id, event_id)
        except Exception:
            logger.exception("seating failed")
            raise HTTPException(status_code=500, detail="The seating arrangement could not be updated.")

    async def get_unassigned_guests(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Sequence[Guest]:
        await self.event_service.get_event_details(event_id, user_id)
        return await self.repo.list_unassigned_guests(event_id)