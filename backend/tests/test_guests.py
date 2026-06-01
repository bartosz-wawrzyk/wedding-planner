import uuid
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from app.modules.guest.models import GuestType, GuestSide, ConfirmationStatus

@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Creates an account for the legitimate owner of the event and returns an authorization header."""
    email = "wedding_owner@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

@pytest.fixture
async def alternative_auth_headers(client: AsyncClient) -> dict:
    """Creates another user's account (a potential attacker) for BOLA/IDOR testing."""
    email = "intruder@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

@pytest.fixture
async def created_event_id(client: AsyncClient, auth_headers: dict) -> uuid.UUID:
    """Creates a valid future event and returns its ID."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
    payload = {"name": "Ślub i Wesele", "date_time": future_date}
    res = await client.post("/events/", json=payload, headers=auth_headers)
    return uuid.UUID(res.json()["id"])

@pytest.fixture
def valid_guest_payload() -> dict:
    """Returns the correct payload for creating a new guest."""
    return {
        "full_name": "Jan Kowalski",
        "guest_type": "adult",
        "side": "groom",
        "confirmation_status": "pending",
        "has_accommodation": False,
        "has_day_after": True,
        "dietary_requirements": "Wege",
        "contact_info": "123456789",
        "position_index": 1
    }


# ---------------------------------------------------------------------------
# SECTION 1: FUNCTIONALITY (HAPPY PATH / CRUD)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_guest_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Functionality: Correct creation of a guest assigned to an event."""
    response = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["full_name"] == valid_guest_payload["full_name"]
    assert data["guest_type"] == "adult"
    assert data["side"] == "groom"


@pytest.mark.asyncio
async def test_get_guests_for_event_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Functionality: Retrieve the full guest list for a specific event."""
                            
    await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    valid_guest_payload["full_name"] = "Anna Nowak"
    await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)

    response = await client.get(f"/events/{created_event_id}/guests/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_guest_details_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Functionality: Retrieve detailed information about a specific guest."""
    create_res = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    guest_id = create_res.json()["id"]

    response = await client.get(f"/events/{created_event_id}/guests/{guest_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == guest_id
    assert response.json()["full_name"] == valid_guest_payload["full_name"]


@pytest.mark.asyncio
async def test_patch_guest_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Functionality: Partial modification of guest data (PATCH)."""
    create_res = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    guest_id = create_res.json()["id"]

    patch_payload = {"confirmation_status": "confirmed", "full_name": "Jan Kowalski - Zmiana"}
    response = await client.patch(f"/events/{created_event_id}/guests/{guest_id}", json=patch_payload, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["confirmation_status"] == "confirmed"
    assert data["full_name"] == "Jan Kowalski - Zmiana"
                                                            
    assert data["dietary_requirements"] == valid_guest_payload["dietary_requirements"]


@pytest.mark.asyncio
async def test_delete_guest_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Functionality: Properly remove a guest from an event."""
    create_res = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    guest_id = create_res.json()["id"]

    delete_res = await client.delete(f"/events/{created_event_id}/guests/{guest_id}", headers=auth_headers)
    assert delete_res.status_code == 204

                                                         
    get_res = await client.get(f"/events/{created_event_id}/guests/{guest_id}", headers=auth_headers)
    assert get_res.status_code == 404


# ---------------------------------------------------------------------------
# SECTION 2: DATA VALIDATION (EDGE CASES)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_guest_empty_or_whitespace_name_fails(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Validation: The guest's first and last name cannot be empty or consist solely of spaces."""
    valid_guest_payload["full_name"] = "   "
    response = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    assert response.status_code == 422

    valid_guest_payload["full_name"] = ""
    response = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_guest_invalid_enum_fields_fails(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Validation: Submitting an invalid value for Enum fields (e.g., side, guest_type) results in a 422 error."""
    valid_guest_payload["side"] = "invalid_side"
    response = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=auth_headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# SECTION 3: SECURITY (BOLA / IDOR / DATA ISOLATION)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_attacker_cannot_create_guest_in_someone_elses_event(client: AsyncClient, alternative_auth_headers: dict, created_event_id: uuid.UUID, valid_guest_payload: dict):
    """Security: An unauthorized user cannot add a guest to someone else's event."""
    response = await client.post(f"/events/{created_event_id}/guests/", json=valid_guest_payload, headers=alternative_auth_headers)
                                                                                       
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_attacker_cannot_list_someone_elses_guests(client: AsyncClient, auth_headers: