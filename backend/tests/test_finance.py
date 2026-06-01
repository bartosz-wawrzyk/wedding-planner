import uuid
import pytest
from decimal import Decimal
from httpx import AsyncClient

# ===========================================================================
# SECTION 1: API FUNCTIONALITY (Happy Path & Business Cycle)
# ===========================================================================

@pytest.fixture
async def register_two_users(client: AsyncClient) -> dict:
    """Registers and logs in two independent users (Victim and Attacker)."""
    v_email = "victim_finance@example.com"
    v_pass = "Password123!"
    await client.post("/auth/register", json={"email": v_email, "password": v_pass})
    v_login = await client.post("/auth/login", json={"email": v_email, "password": v_pass})
    v_token = v_login.json()["access_token"]
    
    v_event_res = await client.post(
        "/events/", 
        json={"name": "Ślub Ofiary", "date_time": "2030-06-30T16:00:00Z"},
        headers={"Authorization": f"Bearer {v_token}"}
    )
    v_event_id = v_event_res.json()["id"]

    a_email = "attacker_finance@example.com"
    a_pass = "Password123!"
    await client.post("/auth/register", json={"email": a_email, "password": a_pass})
    a_login = await client.post("/auth/login", json={"email": a_email, "password": a_pass})
    a_token = a_login.json()["access_token"]
    
    a_event_res = await client.post(
        "/events/", 
        json={"name": "Ślub Atakującego", "date_time": "2030-07-15T17:00:00Z"},
        headers={"Authorization": f"Bearer {a_token}"}
    )
    a_event_id = a_event_res.json()["id"]

    return {
        "victim": {"token": v_token, "headers": {"Authorization": f"Bearer {v_token}"}, "event_id": v_event_id},
        "attacker": {"token": a_token, "headers": {"Authorization": f"Bearer {a_token}"}, "event_id": a_event_id}
    }

@pytest.fixture
async def victim_data(client: AsyncClient, register_two_users: dict) -> dict:
    """Creates a basic expense and payment on the victim's account for detailed testing purposes."""
    env = register_two_users["victim"]
    
    exp_payload = {
        "name": "Sala weselna",
        "category": "FOOD",
        "calculation_strategy": "FIXED",
        "unit_price": "5000.00"
    }
    exp_res = await client.post(f"/events/{env['event_id']}/finance/expenses", json=exp_payload, headers=env["headers"])
    expense_id = exp_res.json()["id"]

    pay_payload = {
        "expense_id": expense_id,
        "amount": "1500.00",
        "paid_by": "Młody",
        "description": "Zaliczka"
    }
    pay_res = await client.post(f"/events/{env['event_id']}/finance/payments", json=pay_payload, headers=env["headers"])
    payment_id = pay_res.json()["id"]

    return {"expense_id": expense_id, "payment_id": payment_id}


@pytest.mark.asyncio
async def test_finance_full_happy_path_cycle(client: AsyncClient, register_two_users: dict):
    """Tests the full functionality of the module: creating an expense, adding a payment, editing, retrieving the list, and summary."""
    env = register_two_users["victim"]
    event_url = f"/events/{env['event_id']}/finance"

    expense_data = {
        "name": "Fotograf Ślubny",
        "category": "SERVICE",
        "calculation_strategy": "FIXED",
        "unit_price": "3500.00",
        "is_included_in_wedding_total": True
    }
    create_exp_res = await client.post(f"{event_url}/expenses", json=expense_data, headers=env["headers"])
    assert create_exp_res.status_code == 201
    expense_id = create_exp_res.json()["id"]

    payment_data = {
        "expense_id": expense_id,
        "amount": "1000.00",
        "paid_by": "Panna Młoda",
        "description": "Zadatek za fotografa"
    }
    create_pay_res = await client.post(f"{event_url}/payments", json=payment_data, headers=env["headers"])
    assert create_pay_res.status_code == 201
    payment_id = create_pay_res.json()["id"]

    get_exp_res = await client.get(f"{event_url}/expenses/{expense_id}", headers=env["headers"])
    assert get_exp_res.status_code == 200
    details = get_exp_res.json()
    assert details["name"] == "Fotograf Ślubny"
    assert Decimal(details["calculated_total_cost"]) == Decimal("3500.00")
    assert Decimal(details["total_paid"]) == Decimal("1000.00")
    assert Decimal(details["remaining_balance"]) == Decimal("2500.00")

    summary_res = await client.get(f"{event_url}/summary", headers=env["headers"])
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert "confirmed" in summary_data
    assert Decimal(summary_data["actual_total"]["total_paid"]) == Decimal("1000.00")

    patch_pay_res = await client.patch(f"{event_url}/payments/{payment_id}", json={"amount": "1200.00"}, headers=env["headers"])
    assert patch_pay_res.status_code == 200
    assert Decimal(patch_pay_res.json()["amount"]) == Decimal("1200.00")

    del_pay_res = await client.delete(f"{event_url}/payments/{payment_id}", headers=env["headers"])
    assert del_pay_res.status_code == 204


# ===========================================================================
# SECTION 2: API RESILIENCE (Edge Cases & Rigorous Input Validation)
# ===========================================================================

@pytest.mark.asyncio
async def test_create_expense_with_blank_name_fails(client: AsyncClient, register_two_users: dict):
    """Resilience: Attempting to submit an expense name consisting only of spaces must be rejected (422)."""
    env = register_two_users["victim"]
    payload = {
        "name": "      ",
        "category": "OTHER",
        "calculation_strategy": "FIXED",
        "unit_price": "100.00"
    }
    response = await client.post(f"/events/{env['event_id']}/finance/expenses", json=payload, headers=env["headers"])
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_expense_invalid_negative_price_fails(client: AsyncClient, register_two_users: dict):
    """Resilience: Negative unit price of an expense is unacceptable (422)."""
    env = register_two_users["victim"]
    payload = {
        "name": "Orkiestra",
        "category": "SERVICE",
        "calculation_strategy": "FIXED",
        "unit_price": "-4500.00"
    }
    response = await client.post(f"/events/{env['event_id']}/finance/expenses", json=payload, headers=env["headers"])
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_payment_with_zero_or_negative_amount_fails(client: AsyncClient, register_two_users: dict, victim_data: dict):
    """Resilience: Payment of an amount less than or equal to 0 must generate a validation error (422)."""
    env = register_two_users["victim"]
    
    for invalid_amount in ["0.00", "-50.00"]:
        payload = {
            "expense_id": victim_data["expense_id"],
            "amount": invalid_amount
        }
        response = await client.post(f"/events/{env['event_id']}/finance/payments", json=payload, headers=env["headers"])
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_custom_multiplier_strategy_validation_constraint(client: AsyncClient, register_two_users: dict):
    """Resilience: Selecting the CUSTOM_MULTIPLIER strategy without providing a multiplier value must trigger an error from model_validator (422)."""
    env = register_two_users["victim"]
    payload = {
        "name": "Napoje premium",
        "category": "ALCOHOL",
        "calculation_strategy": "CUSTOM_MULTIPLIER",
        "unit_price": "15.00",
        "custom_multiplier": None
    }
    response = await client.post(f"/events/{env['event_id']}/finance/expenses", json=payload, headers=env["headers"])
