import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.finance.models import Expense, Payment
from app.modules.event_stats.models import EventGuestSummary

class FinanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_expenses_with_payments(self, event_id: uuid.UUID) -> Sequence[Expense]:
        result = await self.db.execute(
            select(Expense)
            .where(Expense.event_id == event_id)
            .options(selectinload(Expense.payments))
        )
        return result.scalars().all()

    async def create_expense(self, expense: Expense) -> Expense:
        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)
        return expense

    async def create_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def get_expense_by_id(self, expense_id: uuid.UUID, event_id: uuid.UUID) -> Expense | None:
        result = await self.db.execute(
            select(Expense)
            .where(Expense.id == expense_id, Expense.event_id == event_id)
            .options(selectinload(Expense.payments))
        )
        return result.scalar_one_or_none()

    async def get_payment_by_id(self, payment_id: uuid.UUID, event_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(
            select(Payment)
            .join(Expense)
            .where(Payment.id == payment_id, Expense.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def save_expense(self, expense: Expense) -> Expense:
        await self.db.commit()
        await self.db.refresh(expense)
        return expense

    async def save_payment(self, payment: Payment) -> Payment:
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def delete_expense(self, expense: Expense) -> None:
        await self.db.delete(expense)
        await self.db.commit()

    async def delete_payment(self, payment: Payment) -> None:
        await self.db.delete(payment)
        await self.db.commit()
        
    async def get_guest_statistics_from_view(self, event_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(EventGuestSummary).where(EventGuestSummary.event_id == event_id)
        )
        row = result.scalar_one_or_none()

        if not row:
            return [
                {"budget_status": "confirmed", "adults": 0, "children": 0, "guests": 0, "invitations": 0},
                {"budget_status": "pending", "adults": 0, "children": 0, "guests": 0, "invitations": 0},
                {"budget_status": "total", "adults": 0, "children": 0, "guests": 0, "invitations": 0},
            ]

        return [
            {
                "budget_status": "confirmed",
                "adults": row.adults_confirmed or 0,
                "children": row.children_confirmed or 0,
                "guests": row.guests_confirmed or 0,
                "invitations": row.invitations_total or 0,
            },
            {
                "budget_status": "pending",
                "adults": row.adults_pending or 0,
                "children": row.children_pending or 0,
                "guests": row.guests_pending or 0,
                "invitations": row.invitations_total or 0,
            },
            {
                "budget_status": "total",
                "adults": row.adults_total or 0,
                "children": row.children_total or 0,
                "guests": row.total_guests or 0,
                "invitations": row.invitations_total or 0,
            },
        ]