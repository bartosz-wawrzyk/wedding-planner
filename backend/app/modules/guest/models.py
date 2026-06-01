import enum
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.events.models import Event
    from app.modules.invitation.models import Invitation
    from app.modules.table.models import Table

class GuestType(enum.Enum):
    ADULT = "adult"
    CHILD = "child"

class GuestSide(enum.Enum):
    GROOM = "groom"
    BRIDE = "bride"

class ConfirmationStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

class Guest(Base):
    __table_args__ = (
        Index("ix_guest_event_id", "event_id"),
        UniqueConstraint("table_id", "position_index", name="uq_guest_table_position"),
        CheckConstraint("position_index IS NULL OR position_index >= 1", name="check_guest_position_positive"),
        {"schema": "wp"},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wp.event.id", ondelete="CASCADE"), nullable=False)
    invitation_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("wp.invitation.id", ondelete="SET NULL"), nullable=True)
    table_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("wp.table.id", ondelete="SET NULL"), nullable=True)
    position_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guest_type: Mapped[GuestType] = mapped_column(Enum(GuestType), default=GuestType.ADULT, nullable=False)
    side: Mapped[GuestSide] = mapped_column(Enum(GuestSide), nullable=False)
    confirmation_status: Mapped[ConfirmationStatus] = mapped_column(Enum(ConfirmationStatus), default=ConfirmationStatus.PENDING, nullable=False)
    has_accommodation: Mapped[bool] = mapped_column(Boolean, default=False)
    has_day_after: Mapped[bool] = mapped_column(Boolean, default=False)
    dietary_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    invitation: Mapped["Invitation"] = relationship(back_populates="guests")
    event: Mapped["Event"] = relationship(back_populates="guests")
    table: Mapped["Table"] = relationship(back_populates="guests")