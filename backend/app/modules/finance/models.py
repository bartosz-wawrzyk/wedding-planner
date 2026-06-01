import enum
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

class ExpenseCategory(str, enum.Enum):
    FOOD = "FOOD"
    ALCOHOL = "ALCOHOL"
    SERVICE = "SERVICE"
    ATTIRE = "ATTIRE"
    ACCOMMODATION = "ACCOMMODATION"
    OTHER = "OTHER"

class CalculationStrategy(str, enum.Enum):
    FIXED = "FIXED"
    PER_ADULT = "PER_ADULT"
    PER_CHILD = "PER_CHILD"
    PER_GUEST = "PER_GUEST"
    PER_INVITATION = "PER_INVITATION"
    CUSTOM_MULTIPLIER = "CUSTOM_MULTIPLIER"

class Expense(Base):
    __table_args__ = (
        Index("ix_expense_event_id", "event_id"),
        {"schema": "wp"},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wp.event.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory), nullable=False)
    is_included_in_wedding_total: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    calculation_strategy: Mapped[CalculationStrategy] = mapped_column(Enum(CalculationStrategy), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    custom_multiplier: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="expense", cascade="all, delete-orphan"
    )


class Payment(Base):
    __table_args__ = (
        {"schema": "wp"},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wp.expense.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    paid_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    expense: Mapped["Expense"] = relationship("Expense", back_populates="payments")