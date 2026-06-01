import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from .repository import get_event_guest_summary
from .schemas import EventStatsResponse

async def get_event_stats(
    event_id: uuid.UUID,
    db: AsyncSession,
) -> EventStatsResponse:
    summary = await get_event_guest_summary(event_id, db)

    if summary is None:
        return EventStatsResponse.model_validate({
            field: 0 for field in EventStatsResponse.model_fields if field != "model_config"
        })

    return EventStatsResponse.model_validate(summary)