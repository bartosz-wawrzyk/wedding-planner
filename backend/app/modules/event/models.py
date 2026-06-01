import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.invitation.models import Invitation
    from app.modules.table.models import Table
    from app.modules.guest.models import Guest

class Event(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wp.user.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    ceremony_place: Mapped[str] = mapped_column(String(255), nullable=True)
    ceremony_address: Mapped[str] = mapped_column(String(500), nullable=True)
    
    reception_place: Mapped[str] = mapped_column(String(255), nullable=True)
    reception_address: Mapped[str] = mapped_column(String(500), nullable=True)

    invitations: Mapped[List["Invitation"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    tables: Mapped[List["Table"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    guests: Mapped[List["Guest"]] = relationship(back_populates="event", cascade="all, delete-orphan")