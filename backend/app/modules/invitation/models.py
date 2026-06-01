import enum
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.event.models import Event
    from app.modules.guest.models import Guest

class InvitationStatus(str, enum.Enum):
    NOT_DELIVERED = "NOT_DELIVERED"
    DELIVERED = "DELIVERED"

class Invitation(Base):
    __table_args__ = {"schema": "wp"}

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wp.event.id"), nullable=False)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, name="invitationstatus"),
        nullable=False,
        default=InvitationStatus.NOT_DELIVERED,
    )

    event: Mapped["Event"] = relationship(back_populates="invitations")
    guests: Mapped[List["Guest"]] = relationship(
        back_populates="invitation",
        cascade="save-update, merge",
        passive_deletes=True
    )