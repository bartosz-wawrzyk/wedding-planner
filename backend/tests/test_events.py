import uuid
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

@pytest.fixture
async def other_user_token(client: AsyncClient) -> str:
    """Creates a separate user for privilege violation testing (BOLA/IDOR)."""
    email = "other_user_event@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return login_res.json()["access_token"]

@pytest.fixture
def valid_event_payload() -> dict:
    future_date = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0).isoformat()
    return {
        "name": "Wielkie Weselisko",
        "date_time": future_date,
        "ceremony_place": "Kościół św. Anny",
        "ceremony_address": "ul. Centralna 15, Kraków",
        "reception_place": "Sala Bankietowa Złota Róża",
        "reception_address": "ul. Ogrodowa 44, Wieliczka"
    }


# ---------------------------------------------------------------------------
# SECTION 1: HAPPY PATH / CORRECT CRUD OPERATIONS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_event_success(client: AsyncClient, valid_event_payload: dict):
    """Test of correct event creation with full data."""
    await client.post("/auth/register", json={"email": "owner_event@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "owner_event@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.post("/events/", json=valid_event_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == valid_event_payload["name"]
    assert data["ceremony_place"] == valid_event_payload["ceremony_place"]


@pytest.mark.asyncio
async def test_get_all_events_for_logged_user(client: AsyncClient, valid_event_payload: dict):
    """Test of downloading the list of events assigned to the logged in user."""
    await client.post("/auth/register", json={"email": "lister@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "lister@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    await client.post("/events/", json=valid_event_payload, headers=headers)
    valid_event_payload["name"] = "Drugie Wydarzenie"
    await client.post("/events/", json=valid_event_payload, headers=headers)

    response = await client.get("/events/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_single_event_details_success(client: AsyncClient, valid_event_payload: dict):
    """Test of retrieving details of a specific event by the owner."""
    await client.post("/auth/register", json={"email": "detailer@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "detailer@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=headers)
    event_id = create_res.json()["id"]

    response = await client.get(f"/events/{event_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == event_id


@pytest.mark.asyncio
async def test_update_event_partial_success(client: AsyncClient, valid_event_payload: dict):
    """Test of partial update (PATCH) of event fields by the owner."""
    await client.post("/auth/register", json={"email": "patcher@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "patcher@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=headers)
    event_id = create_res.json()["id"]

    updated_fields = {"name": "Nowa Nazwa Wesela", "ceremony_place": "Urząd Stanu Cywilnego"}
    response = await client.patch(f"/events/{event_id}", json=updated_fields, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nowa Nazwa Wesela"
    assert data["ceremony_place"] == "Urząd Stanu Cywilnego"
    assert data["ceremony_address"] == valid_event_payload["ceremony_address"]


@pytest.mark.asyncio
async def test_delete_event_success(client: AsyncClient, valid_event_payload: dict):
    """Test of correct deletion of the event by the owner."""
    await client.post("/auth/register", json={"email": "deleter@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "deleter@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=headers)
    event_id = create_res.json()["id"]

    delete_res = await client.delete(f"/events/{event_id}", headers=headers)
    assert delete_res.status_code == 204

    get_res = await client.get(f"/events/{event_id}", headers=headers)
    assert get_res.status_code == 404


# ---------------------------------------------------------------------------
# SECTION 2: VALIDATION AND TIME (TIME ZONES)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_event_past_date_fails(client: AsyncClient, valid_event_payload: dict):
    """Validation: Past event date must be rejected (422)."""
    await client.post("/auth/register", json={"email": "validator_event@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "validator_event@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    valid_event_payload["date_time"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    
    response = await client.post("/events/", json=valid_event_payload, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_event_to_past_date_fails(client: AsyncClient, valid_event_payload: dict):
    """Validation: Attempting to change the date to the past during an update must be blocked."""
    await client.post("/auth/register", json={"email": "date_patcher@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "date_patcher@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=headers)
    event_id = create_res.json()["id"]

    past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    response = await client.patch(f"/events/{event_id}", json={"date_time": past_date}, headers=headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# SECTION 3: SECURITY (BOLA / IDOR / DATA ISOLATION)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_other_user_event_returns_404(client: AsyncClient, valid_event_payload: dict, other_user_token: str):
    """Security: User cannot download another user's single event.""""
    await client.post("/auth/register", json={"email": "real_owner_event@example.com", "password": "Password123!"})
    login_owner = await client.post("/auth/login", json={"email": "real_owner_event@example.com", "password": "Password123!"})
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=owner_headers)
    event_id = create_res.json()["id"]

    attacker_headers = {"Authorization": f"Bearer {other_user_token}"}
    response = await client.get(f"/events/{event_id}", headers=attacker_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_other_user_event_returns_404(client: AsyncClient, valid_event_payload: dict, other_user_token: str):
    """Security: A user cannot modify (PATCH) an event belonging to someone else."""
    await client.post("/auth/register", json={"email": "owner_update_event@example.com", "password": "Password123!"})
    login_owner = await client.post("/auth/login", json={"email": "owner_update_event@example.com", "password": "Password123!"})
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=owner_headers)
    event_id = create_res.json()["id"]

    attacker_headers = {"Authorization": f"Bearer {other_user_token}"}
    response = await client.patch(f"/events/{event_id}", json={"name": "Zhakowane Wesele"}, headers=attacker_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_user_event_returns_404(client: AsyncClient, valid_event_payload: dict, other_user_token: str):
    """Security: A user cannot delete an event belonging to someone else."""
    await client.post("/auth/register", json={"email": "owner_delete_event@example.com", "password": "Password123!"})
    login_owner = await client.post("/auth/login", json={"email": "owner_delete_event@example.com", "password": "Password123!"})
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    create_res = await client.post("/events/", json=valid_event_payload, headers=owner_headers)
    event_id = create_res.json()["id"]

    attacker_headers = {"Authorization": f"Bearer {other_user_token}"}
    response = await client.delete(f"/events/{event_id}", headers=attacker_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_all_events_does_not_leak_other_users_data(client: AsyncClient, valid_event_payload: dict, other_user_token: str):
    """Security: Downloading a list of all events cannot reveal other users' records."""
    await client.post("/auth/register", json={"email": "isolated_owner@example.com", "password": "Password123!"})
    login_owner = await client.post("/auth/login", json={"email": "isolated_owner@example.com", "password": "Password123!"})
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    await client.post("/events/", json=valid_event_payload, headers=owner_headers)

    attacker_headers = {"Authorization": f"Bearer {other_user_token}"}
    response = await client.get("/events/", headers=attacker_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


# ---------------------------------------------------------------------------
# SECTION 4: EDGE CASES
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_non_existent_event_returns_404(client: AsyncClient):
    """Extreme case: Querying for a randomly generated event UUID results in a 404 error."""
    await client.post("/auth/register", json={"email": "random_user@example.com", "password": "Password123!"})
    login = await client.post("/auth/login", json={"email": "random_user@example.com", "password": "Password123!"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    random_id = uuid.uuid4()
    response = await client.get(f"/events/{random_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access_blocked(client: AsyncClient):
    """Extreme case: Lack of authorization token blocks access to event endpoints (401)."""
    response = await client.get("/events/")
    assert response.status_code == 401

    response_post = await client.post("/events/", json={})
    assert response_post.status_code == 401