import uuid
import logging
from decimal import Decimal
from fastapi import HTTPException, status
from typing import Sequence

from app.modules.finance.repository import FinanceRepository
from app.modules.finance.models import Expense, Payment, CalculationStrategy
from app.modules.finance.schemas import (
    ExpenseCreate, 
    PaymentCreate, 
    BudgetStatusSummary, 
    ExpenseBreakdownItem, 
    FinanceSummaryResponse, 
    ExpenseUpdate, 
    PaymentUpdate,
    ExpenseDetailResponse
)
from app.modules.event.service import EventService

logger = logging.getLogger(__name__)

class GuestStatsDTO:
    def __init__(self, adults: int, children: int, guests: int, invitations: int):
        self.adults = Decimal(adults)
        self.children = Decimal(children)
        self.guests = Decimal(guests)
        self.invitations = Decimal(invitations)

class FinanceService:
    def __init__(self, repo: FinanceRepository, event_service: EventService):
        self.repo = repo
        self.event_service = event_service

    async def create_expense(self, event_id: uuid.UUID, data: ExpenseCreate, user_id: uuid.UUID) -> Expense:
        await self.event_service.get_event_details(event_id, user_id)
        expense = Expense(**data.model_dump(), event_id=event_id)
        created = await self.repo.create_expense(expense)
        logger.info("Created expense id=%s event_id=%s", created.id, event_id)
        return created

    async def get_expenses(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Sequence[Expense]:
        await self.event_service.get_event_details(event_id, user_id)
        return await self.repo.get_expenses_with_payments(event_id)

    async def get_expense_details(self, expense_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> ExpenseDetailResponse:
        await self.event_service.get_event_details(event_id, user_id)

        expense = await self.repo.get_expense_by_id(expense_id, event_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The expense does not exist")

        total_paid = sum(p.amount for p in expense.payments)
        calculated_total_cost = expense.unit_price * (expense.custom_multiplier or 1)
        remaining_balance = calculated_total_cost - total_paid

        expense_data = {
            "id": expense.id,
            "name": expense.name,
            "category": expense.category,
            "is_included_in_wedding_total": expense.is_included_in_wedding_total,
            "calculation_strategy": expense.calculation_strategy,
            "unit_price": expense.unit_price,
            "custom_multiplier": expense.custom_multiplier,
        }

        return ExpenseDetailResponse(
            **expense_data,
            payments=expense.payments,
            calculated_total_cost=calculated_total_cost,
            total_paid=total_paid,
            remaining_balance=remaining_balance
        )

    async def update_expense(self, expense_id: uuid.UUID, event_id: uuid.UUID, data: ExpenseUpdate, user_id: uuid.UUID) -> Expense:
        await self.event_service.get_event_details(event_id, user_id)
        expense = await self.repo.get_expense_by_id(expense_id, event_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The expense does not exist")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(expense, key, value)
            
        return await self.repo.save_expense(expense)

    async def delete_expense(self, expense_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.event_service.get_event_details(event_id, user_id)
        expense = await self.repo.get_expense_by_id(expense_id, event_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The expense does not exist")
        await self.repo.delete_expense(expense)

    async def create_payment(self, event_id: uuid.UUID, data: PaymentCreate, user_id: uuid.UUID) -> Payment:
        await self.event_service.get_event_details(event_id, user_id)
        expense = await self.repo.get_expense_by_id(data.expense_id, event_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="The expense does not exist or does not belong to this event"
            )
        payment = Payment(**data.model_dump())
        return await self.repo.create_payment(payment)

    async def get_payment_details(self, payment_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> Payment:
        await self.event_service.get_event_details(event_id, user_id)
        payment = await self.repo.get_payment_by_id(payment_id, event_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The payment does not exist")
        return payment

    async def update_payment(self, payment_id: uuid.UUID, event_id: uuid.UUID, data: PaymentUpdate, user_id: uuid.UUID) -> Payment:
        await self.event_service.get_event_details(event_id, user_id)
        payment = await self.repo.get_payment_by_id(payment_id, event_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The payment does not exist or is not associated with this event")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(payment, key, value)
            
        return await self.repo.save_payment(payment)

    async def delete_payment(self, payment_id: uuid.UUID, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.event_service.get_event_details(event_id, user_id)
        payment = await self.repo.get_payment_by_id(payment_id, event_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The payment does not exist or is not associated with this event")
        await self.repo.delete_payment(payment)

    async def generate_finance_summary(self, event_id: uuid.UUID, user_id: uuid.UUID) -> FinanceSummaryResponse:
        await self.event_service.get_event_details(event_id, user_id)

        expenses = await self.repo.get_expenses_with_payments(event_id)
        raw_stats = await self.repo.get_guest_statistics_from_view(event_id)

        stats_map = {}
        for row in raw_stats:
            stats_map[row["budget_status"].lower()] = GuestStatsDTO(
                adults=row["adults"],
                children=row["children"],
                guests=row["guests"],
                invitations=row["invitations"]
            )

        empty_stats = GuestStatsDTO(0, 0, 0, 0)

        confirmed_summary, _ = self._build_status_summary(expenses, stats_map.get("confirmed", empty_stats))
        pending_summary, _ = self._build_status_summary(expenses, stats_map.get("pending", empty_stats))
        actual_total_summary, breakdown = self._build_status_summary(expenses, stats_map.get("total", empty_stats))

        return FinanceSummaryResponse(
            confirmed=confirmed_summary,
            pending=pending_summary,
            actual_total=actual_total_summary,
            breakdown=breakdown
        )

    def _calculate_expense_cost(self, expense: Expense, stats: GuestStatsDTO) -> Decimal:
        strategies = {
            CalculationStrategy.FIXED: lambda: expense.unit_price,
            CalculationStrategy.PER_ADULT: lambda: expense.unit_price * stats.adults,
            CalculationStrategy.PER_CHILD: lambda: expense.unit_price * stats.children,
            CalculationStrategy.PER_GUEST: lambda: expense.unit_price * stats.guests,
            CalculationStrategy.PER_INVITATION: lambda: expense.unit_price * stats.invitations,
            CalculationStrategy.CUSTOM_MULTIPLIER: lambda: expense.unit_price * (expense.custom_multiplier or Decimal(0))
        }
        
        strategy_func = strategies.get(expense.calculation_strategy)
        if not strategy_func:
            logger.error("Unknown calculation strategy: %s", expense.calculation_strategy)
            return Decimal(0)
            
        return strategy_func()

    def _build_status_summary(self, expenses: Sequence[Expense], stats: GuestStatsDTO) -> tuple[BudgetStatusSummary, list[ExpenseBreakdownItem]]:
        wedding_costs_total = Decimal(0)
        couple_costs_total = Decimal(0)
        fixed_costs_wedding = Decimal(0)
        fixed_costs_couple = Decimal(0)
        total_paid = Decimal(0)
        
        by_category = {}
        breakdown: list[ExpenseBreakdownItem] = []

        for expense in expenses:
            cost = self._calculate_expense_cost(expense, stats)
            expense_paid = sum(p.amount for p in expense.payments)
            total_paid += expense_paid

            if expense.is_included_in_wedding_total:
                wedding_costs_total += cost
                if expense.calculation_strategy == CalculationStrategy.FIXED:
                    fixed_costs_wedding += cost
            else:
                couple_costs_total += cost
                if expense.calculation_strategy == CalculationStrategy.FIXED:
                    fixed_costs_couple += cost

            by_category[expense.category] = by_category.get(expense.category, Decimal(0)) + cost

            breakdown.append(ExpenseBreakdownItem(
                id=expense.id,
                name=expense.name,
                category=expense.category,
                strategy=expense.calculation_strategy,
                unit_price=expense.unit_price,
                calculated_cost=cost,
                is_included_in_wedding=expense.is_included_in_wedding_total
            ))

        summary = BudgetStatusSummary(
            wedding_costs_total=wedding_costs_total,
            couple_costs_total=couple_costs_total,
            fixed_costs_wedding=fixed_costs_wedding,
            fixed_costs_couple=fixed_costs_couple,
            total_paid=total_paid,
            total_remaining=(wedding_costs_total + couple_costs_total) - total_paid,
            by_category=by_category,
            breakdown=breakdown
        )

        return summary, breakdown