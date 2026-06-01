import uuid
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    email = "invitation_owner@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

@pytest.fixture
async def alternative_auth_headers(client: AsyncClient) -> dict:
    email = "invitation_intruder@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}

@pytest.fixture
async def created_event_id(client: AsyncClient, auth_headers: dict) -> uuid.UUID:
    future_date = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    payload = {"name": "Wesele Marzeń", "date_time": future_date}
    res = await client.post("/events/", json=payload, headers=auth_headers)
    return uuid.UUID(res.json()["id"])

@pytest.fixture
async def created_guest_id(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID) -> uuid.UUID:
    payload = {"full_name": "Antoni Kowalski", "guest_type": "adult", "side": "bride"}
    res = await client.post(f"/events/{created_event_id}/guests/", json=payload, headers=auth_headers)
    return uuid.UUID(res.json()["id"])

# ---------------------------------------------------------------------------
# SECTION 1: FUNCTIONALITY (HAPPY PATH / CRUD)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_invitation_without_guests(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID):
    payload = {"group_name": "Rodzina Kowalskich", "guest_ids": []}
    response = await client.post(f"/events/{created_event_id}/invitations/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["group_name"] == "Rodzina Kowalskich"
    assert data["guests"] == []
    assert "id" in data

@pytest.mark.asyncio
async def test_create_invitation_with_existing_guests(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, created_guest_id: uuid.UUID):
    payload = {"group_name": "Rodzina Antoniego", "guest_ids": [str(created_guest_id)]}
    response = await client.post(f"/events/{created_event_id}/invitations/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data["guests"]) == 1
    assert data["guests"][0]["id"] == str(created_guest_id)

@pytest.mark.asyncio
async def test_get_invitations_for_event_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID):
    payload = {"group_name": "Grupa A", "guest_ids": []}
    await client.post(f"/events/{created_event_id}/invitations/", json=payload, headers=auth_headers)
    
    response = await client.get(f"/events/{created_event_id}/invitations/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_patch_invitation_replace_guests(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, created_guest_id: uuid.UUID):
    inv_payload = {"group_name": "Pierwsza Grupa", "guest_ids": [str(created_guest_id)]}
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json=inv_payload, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    guest_payload = {"full_name": "Ewa Nowak", "guest_type": "adult", "side": "groom"}
    guest2_res = await client.post(f"/events/{created_event_id}/guests/", json=guest_payload, headers=auth_headers)
    guest2_id = guest2_res.json()["id"]

    patch_payload = {"guest_ids": [str(guest2_id)]}
    response = await client.patch(f"/events/{created_event_id}/invitations/{inv_id}", json=patch_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["guests"]) == 1
    assert data["guests"][0]["id"] == str(guest2_id)

@pytest.mark.asyncio
async def test_update_invitation_status_success(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID):
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json={"group_name": "Test Status"}, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    response = await client.patch(f"/events/{created_event_id}/invitations/{inv_id}/status", json={"status": "DELIVERED"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"

@pytest.mark.asyncio
async def test_delete_invitation_detaches_guests_safely(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID, created_guest_id: uuid.UUID):
    inv_payload = {"group_name": "Tymczasowa Grupa", "guest_ids": [str(created_guest_id)]}
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json=inv_payload, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    delete_res = await client.delete(f"/events/{created_event_id}/invitations/{inv_id}", headers=auth_headers)
    assert delete_res.status_code == 204

    guest_res = await client.get(f"/events/{created_event_id}/guests/{created_guest_id}", headers=auth_headers)
    assert guest_res.status_code == 200
    assert guest_res.json()["invitation_id"] is None

# ---------------------------------------------------------------------------
# SECTION 2: DATA VALIDATION (EXTREME CASES / ROBUSTNESS)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_invitation_with_invalid_guest_id_fails(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID):
    payload = {"group_name": "Oszukane Zaproszenie", "guest_ids": [str(uuid.uuid4())]}
    response = await client.post(f"/events/{created_event_id}/invitations/", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Nie znaleziono gości o ID" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_invitation_invalid_enum_status_fails(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID):
    payload = {"group_name": "Grupa", "status": "INVALID_STATUS"}
    response = await client.post(f"/events/{created_event_id}/invitations/", json=payload, headers=auth_headers)
    assert response.status_code == 422

                                                                                                
                                                                             
@pytest.mark.asyncio
async def test_create_invitation_empty_group_name_fails(client: AsyncClient, auth_headers: dict, created_event_id: uuid.UUID):
    response = await client.post(f"/events/{created_event_id}/invitations/", json={"group_name": "   "}, headers=auth_headers)
    assert response.status_code == 422

# ---------------------------------------------------------------------------
# SECTION 3: SECURITY (BOLA / IDOR / AUTHORIZATION)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_attacker_cannot_create_invitation_in_someone_elses_event(client: AsyncClient, alternative_auth_headers: dict, created_event_id: uuid.UUID):
    payload = {"group_name": "Atak", "guest_ids": []}
    response = await client.post(f"/events/{created_event_id}/invitations/", json=payload, headers=alternative_auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_attacker_cannot_list_someone_elses_invitations(client: AsyncClient, alternative_auth_headers: dict, created_event_id: uuid.UUID):
    response = await client.get(f"/events/{created_event_id}/invitations/", headers=alternative_auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_attacker_cannot_get_someone_elses_invitation(client: AsyncClient, auth_headers: dict, alternative_auth_headers: dict, created_event_id: uuid.UUID):
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json={"group_name": "Tajne"}, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    response = await client.get(f"/events/{created_event_id}/invitations/{inv_id}", headers=alternative_auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_attacker_cannot_patch_someone_elses_invitation(client: AsyncClient, auth_headers: dict, alternative_auth_headers: dict, created_event_id: uuid.UUID):
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json={"group_name": "Do Edycji"}, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    response = await client.patch(f"/events/{created_event_id}/invitations/{inv_id}", json={"group_name": "Zhakowane"}, headers=alternative_auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_attacker_cannot_update_status_of_someone_elses_invitation(client: AsyncClient, auth_headers: dict, alternative_auth_headers: dict, created_event_id: uuid.UUID):
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json={"group_name": "Status Atak"}, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    response = await client.patch(f"/events/{created_event_id}/invitations/{inv_id}/status", json={"status": "DELIVERED"}, headers=alternative_auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_attacker_cannot_delete_someone_elses_invitation(client: AsyncClient, auth_headers: dict, alternative_auth_headers: dict, created_event_id: uuid.UUID):
    inv_res = await client.post(f"/events/{created_event_id}/invitations/", json={"group_name": "Do Usunięcia"}, headers=auth_headers)
    inv_id = inv_res.json()["id"]

    response = await client.delete(f"/events/{created_event_id}/invitations/{inv_id}", headers=alternative_auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_unauthorized_invitation_access_blocked(client: AsyncClient, created_event_id: uuid.UUID):
    response = await client.get(f"/events/{created_event_id}/invitations/")
    assert response.status_code == 401

    response_post = await client.post(f"/events/{created_event_id}/invitations/", json={})
    assert response_post.status_code == 401