import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.router import get_current_user
from app.modules.event.repository import EventRepository
from app.modules.event.service import EventService
from app.modules.finance.repository import FinanceRepository
from app.modules.finance.service import FinanceService
from app.modules.finance.schemas import (
    ExpenseCreate, PaymentCreate, ExpenseResponse, PaymentResponse,
    ExpenseDetailResponse, ExpenseUpdate, PaymentUpdate, FinanceSummaryResponse
)

router = APIRouter(prefix="/events/{event_id}/finance", tags=["finance"])

def get_finance_service(db: AsyncSession = Depends(get_db)) -> FinanceService:
    event_repo = EventRepository(db)
    event_service = EventService(event_repo)
    finance_repo = FinanceRepository(db)
    return FinanceService(finance_repo, event_service)


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    event_id: uuid.UUID,
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> ExpenseResponse:
    return await service.create_expense(event_id, data, current_user.id)

@router.get("/expenses/{expense_id}", response_model=ExpenseDetailResponse)
async def get_expense_details(
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> ExpenseDetailResponse:
    return await service.get_expense_details(expense_id, event_id, current_user.id)

@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> ExpenseResponse:
    return await service.update_expense(expense_id, event_id, data, current_user.id)

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> None:
    await service.delete_expense(expense_id, event_id, current_user.id)


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    event_id: uuid.UUID,
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> PaymentResponse:
    return await service.create_payment(event_id, data, current_user.id)

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment_details(
    event_id: uuid.UUID,
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> PaymentResponse:
    return await service.get_payment_details(payment_id, event_id, current_user.id)

@router.patch("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    event_id: uuid.UUID,
    payment_id: uuid.UUID,
    data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> PaymentResponse:
    return await service.update_payment(payment_id, event_id, data, current_user.id)

@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    event_id: uuid.UUID,
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> None:
    await service.delete_payment(payment_id, event_id, current_user.id)
    

@router.get("/summary", response_model=FinanceSummaryResponse)
async def get_finance_summary(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> FinanceSummaryResponse:
    return await service.generate_finance_summary(event_id, current_user.id)