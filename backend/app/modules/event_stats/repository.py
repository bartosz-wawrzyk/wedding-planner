import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import EventGuestSummary


async def get_event_guest_summary(
    event_id: uuid.UUID,
    db: AsyncSession,
) -> EventGuestSummary | None:
    result = await db.execute(
        select(EventGuestSummary).where(EventGuestSummary.event_id == event_id)
    )
    return result.scalar_one_or_none()