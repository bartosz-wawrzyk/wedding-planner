import uuid
from decimal import Decimal
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator, StringConstraints
from app.modules.finance.models import ExpenseCategory, CalculationStrategy

CleanStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]

class ExpenseCreate(BaseModel):
    name: CleanStr
    category: ExpenseCategory
    is_included_in_wedding_total: bool = True
    calculation_strategy: CalculationStrategy
    unit_price: Decimal = Field(..., ge=0)
    custom_multiplier: Decimal | None = Field(None, ge=0)

    @model_validator(mode='after')
    def validate_multiplier(self) -> 'ExpenseCreate':
        if self.calculation_strategy == CalculationStrategy.CUSTOM_MULTIPLIER and self.custom_multiplier is None:
            raise ValueError("The CUSTOM_MULTIPLIER strategy requires you to specify a custom_multiplier.")
        return self

class PaymentCreate(BaseModel):
    expense_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    paid_by: str | None = None
    description: str | None = None

class ExpenseResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: ExpenseCategory
    is_included_in_wedding_total: bool
    calculation_strategy: CalculationStrategy
    unit_price: Decimal
    custom_multiplier: Decimal | None

    model_config = ConfigDict(from_attributes=True)

class PaymentResponse(BaseModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    amount: Decimal
    paid_by: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExpenseDetailResponse(ExpenseResponse):
    payments: list[PaymentResponse] = []
    calculated_total_cost: Decimal
    total_paid: Decimal
    remaining_balance: Decimal

class ExpenseUpdate(BaseModel):
    name: CleanStr | None = Field(None)
    category: ExpenseCategory | None = None
    is_included_in_wedding_total: bool | None = None
    calculation_strategy: CalculationStrategy | None = None
    unit_price: Decimal | None = Field(None, ge=0)
    custom_multiplier: Decimal | None = Field(None, ge=0)

    @model_validator(mode='after')
    def validate_multiplier(self) -> 'ExpenseUpdate':
        if self.calculation_strategy == CalculationStrategy.CUSTOM_MULTIPLIER and self.custom_multiplier is None:
            raise ValueError("The CUSTOM_MULTIPLIER strategy requires you to specify a custom_multiplier.")
        return self

class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0)
    paid_by: str | None = None
    description: str | None = None

class ExpenseBreakdownItem(BaseModel):
    id: uuid.UUID
    name: str
    category: ExpenseCategory
    strategy: CalculationStrategy
    unit_price: Decimal
    calculated_cost: Decimal
    is_included_in_wedding: bool

class BudgetStatusSummary(BaseModel):
    wedding_costs_total: Decimal
    couple_costs_total: Decimal
    fixed_costs_wedding: Decimal
    fixed_costs_couple: Decimal
    total_paid: Decimal
    total_remaining: Decimal
    by_category: dict[ExpenseCategory, Decimal]

class FinanceSummaryResponse(BaseModel):
    confirmed: BudgetStatusSummary
    pending: BudgetStatusSummary
    actual_total: BudgetStatusSummary
    breakdown: list[ExpenseBreakdownItem]