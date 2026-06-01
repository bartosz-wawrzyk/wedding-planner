import enum
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.events.models import Event
    from app.modules.guest.models import Guest

class TableShape(enum.Enum):
    ROUND = "round"
    RECTANGULAR = "rectangular"

class Table(Base):
    __table_args__ = (
        Index("ix_table_event_id", "event_id"),
        CheckConstraint("capacity > 0", name="check_table_capacity_positive"),
        CheckConstraint("number > 0", name="check_table_number_positive"),
        {"schema": "wp"},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wp.event.id", ondelete="CASCADE"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shape: Mapped[TableShape] = mapped_column(Enum(TableShape), default=TableShape.ROUND, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped["Event"] = relationship(back_populates="tables")
    guests: Mapped[List["Guest"]] = relationship(back_populates="table", lazy="selectin")