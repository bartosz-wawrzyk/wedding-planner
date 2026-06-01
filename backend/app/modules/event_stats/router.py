import uuid
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.router import get_current_user
from app.modules.event.repository import EventRepository
from app.modules.event.service import EventService
from app.modules.event_stats.schemas import EventStatsResponse
from .service import get_event_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events/{event_id}", tags=["event-stats"])


def get_events_service(db: AsyncSession = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)


@router.get("/stats", response_model=EventStatsResponse)
async def get_event_stats_endpoint(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_events_service),
) -> EventStatsResponse:
    await event_service.get_event_details(event_id, current_user.id)

    return await get_event_stats(event_id, db)