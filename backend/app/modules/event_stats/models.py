import uuid
from sqlalchemy import Column, Integer, Table, MetaData
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

POSTGRES_SCHEMA = "wp"

event_guest_summary_table = Table(
    "event_guest_summary",
    Base.metadata,
    Column("event_id", UUID(as_uuid=True), primary_key=True),
    Column("total_guests", Integer),
    Column("guests_confirmed", Integer),
    Column("guests_pending", Integer),
    Column("guests_rejected", Integer),
    
    Column("adults_total", Integer),
    Column("children_total", Integer),
    Column("bride_guests_total", Integer),
    Column("groom_guests_total", Integer),
    
    Column("adults_confirmed", Integer),
    Column("children_confirmed", Integer),
    Column("bride_adults_confirmed", Integer),
    Column("bride_children_confirmed", Integer),
    Column("groom_adults_confirmed", Integer),
    Column("groom_children_confirmed", Integer),
    
    Column("adults_pending", Integer),
    Column("children_pending", Integer),
    Column("bride_adults_pending", Integer),
    Column("bride_children_pending", Integer),
    Column("groom_adults_pending", Integer),
    Column("groom_children_pending", Integer),
    
    Column("invitations_total", Integer),
    Column("invitations_bride", Integer),
    Column("invitations_groom", Integer),
    
    Column("accommodation_confirmed", Integer),
    Column("accommodation_pending", Integer),
    schema=POSTGRES_SCHEMA,
    keep_existing=True,
)

class EventGuestSummary:
    pass

Base.registry.map_imperatively(
    EventGuestSummary,
    event_guest_summary_table,
)