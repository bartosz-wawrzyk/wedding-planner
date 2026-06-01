import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.modules.table.models import Table
from app.modules.guest.models import Guest

class TableRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_event(self, table_id: uuid.UUID, event_id: uuid.UUID) -> Table | None:
        result = await self.db.execute(
            select(Table)
            .options(selectinload(Table.guests))
            .where(
                Table.id == table_id,
                Table.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_event(self, event_id: uuid.UUID) -> Sequence[Table]:
        result = await self.db.execute(
            select(Table)
            .where(Table.event_id == event_id)
            .order_by(Table.number)
        )
        return result.scalars().all()

    async def create(self, table: Table) -> Table:
        self.db.add(table)
        await self.db.commit()
        await self.db.refresh(table)
        return table

    async def save(self, table: Table) -> Table:
        await self.db.commit()
        await self.db.refresh(table)
        return table

    async def delete(self, table: Table) -> None:
        await self.db.delete(table)
        await self.db.commit()

    async def get_guests_by_ids_and_event(self, guest_ids: list[uuid.UUID], event_id: uuid.UUID) -> list[Guest]:
        if not guest_ids:
            return []
        result = await self.db.execute(
            select(Guest).where(
                Guest.id.in_(guest_ids),
                Guest.event_id == event_id,
            )
        )
        return list(result.scalars().all())

    async def get_guest_assigned_to_table(self, guest_id: uuid.UUID, table_id: uuid.UUID, event_id: uuid.UUID) -> Guest | None:
        result = await self.db.execute(
            select(Guest).where(
                Guest.id == guest_id,
                Guest.table_id == table_id,
                Guest.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_unassigned_guests(self, event_id: uuid.UUID) -> Sequence[Guest]:
        result = await self.db.execute(
            select(Guest)
            .where(
                Guest.event_id == event_id,
                or_(
                    Guest.table_id.is_(None),
                    Guest.position_index.is_(None),
                ),
            )
            .order_by(Guest.full_name)
        )
        return result.scalars().all()