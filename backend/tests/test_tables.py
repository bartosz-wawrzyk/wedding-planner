import uuid
import pytest
from httpx import AsyncClient

@pytest.fixture
async def owner_token(client: AsyncClient) -> str:
    email = "table_owner@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return login_res.json()["access_token"]

@pytest.fixture
async def other_user_token(client: AsyncClient) -> str:
    email = "table_stranger@example.com"
    password = "Password123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    return login_res.json()["access_token"]

@pytest.fixture
async def active_event_id(client: AsyncClient, owner_token: str) -> uuid.UUID:
    headers = {"Authorization": f"Bearer {owner_token}"}
    payload = {
        "name": "Wesele Testowe",
        "date_time": "2030-01-01T18:00:00Z",
        "ceremony_place": "Kościół",
        "ceremony_address": "Adres",
        "reception_place": "Sala",
        "reception_address": "Adres"
    }
    res = await client.post("/events/", json=payload, headers=headers)
    return uuid.UUID(res.json()["id"])

@pytest.fixture
def valid_table_payload() -> dict:
    return {
        "number": 5,
        "name": "Stół Prezydialny",
        "shape": "round",
        "capacity": 10
    }

# ---------------------------------------------------------------------------
# SECTION 1: API FUNCTIONALITY (Happy Path & Business Logic)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_table_success(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    response = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["number"] == valid_table_payload["number"]
    assert data["name"] == valid_table_payload["name"]
    assert "id" in data
    assert data["event_id"] == str(active_event_id)

@pytest.mark.asyncio
async def test_list_tables_for_event(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    
    response = await client.get(f"/events/{active_event_id}/tables/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_patch_table_success(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    table_id = create_res.json()["id"]

    update_payload = {"name": "Nowa Nazwa Stołu", "capacity": 12}
    response = await client.patch(f"/events/{active_event_id}/tables/{table_id}", json=update_payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nowa Nazwa Stołu"
    assert data["capacity"] == 12

@pytest.mark.asyncio
async def test_delete_table_success(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    table_id = create_res.json()["id"]

    delete_res = await client.delete(f"/events/{active_event_id}/tables/{table_id}", headers=headers)
    assert delete_res.status_code == 204

    get_res = await client.get(f"/events/{active_event_id}/tables/{table_id}", headers=headers)
    assert get_res.status_code == 404

# ---------------------------------------------------------------------------
# SECTION 2: API RESILIENCE (Edge Cases, Validation Errors, Input Integrity)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_table_invalid_capacity_fails(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    valid_table_payload["capacity"] = 0

    response = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_table_invalid_number_fails(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    valid_table_payload["number"] = -1

    response = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_seating_capacity_exceeded_fails(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID):
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    small_table = {"number": 12, "shape": "round", "capacity": 1}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=small_table, headers=headers)
    table_id = create_res.json()["id"]

                                                      
    assignments = [
        {"guest_id": str(uuid.uuid4()), "position_index": 1},
        {"guest_id": str(uuid.uuid4()), "position_index": 2}
    ]
    
    response = await client.put(f"/events/{active_event_id}/tables/{table_id}/seating", json=assignments, headers=headers)
    assert response.status_code == 400
    assert "capacity" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_seating_duplicate_positions_fails(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID):
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    table_payload = {"number": 13, "shape": "round", "capacity": 5}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=table_payload, headers=headers)
    table_id = create_res.json()["id"]

                                                              
    assignments = [
        {"guest_id": str(uuid.uuid4()), "position_index": 1},
        {"guest_id": str(uuid.uuid4()), "position_index": 1}
    ]

    response = await client.put(f"/events/{active_event_id}/tables/{table_id}/seating", json=assignments, headers=headers)
    assert response.status_code == 400
    assert "Duplicate positions" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_seating_invalid_position_index_fails(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID):
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    table_payload = {"number": 14, "shape": "round", "capacity": 5}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=table_payload, headers=headers)
    table_id = create_res.json()["id"]

                                                      
    assignments = [
        {"guest_id": str(uuid.uuid4()), "position_index": 0}
    ]

    response = await client.put(f"/events/{active_event_id}/tables/{table_id}/seating", json=assignments, headers=headers)
    assert response.status_code == 422

# ---------------------------------------------------------------------------
# SECTION 3: DATA SECURITY AND ISOLATION (Data Isolation & Authentication Constraints)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_attacker_cannot_access_or_modify_someone_elses_table(
    client: AsyncClient, owner_token: str, other_user_token: str, active_event_id: uuid.UUID, valid_table_payload: dict
):
    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers_owner)
    table_id = create_res.json()["id"]

    headers_attacker = {"Authorization": f"Bearer {other_user_token}"}
    
                                                  
    res_get = await client.get(f"/events/{active_event_id}/tables/{table_id}", headers=headers_attacker)
    assert res_get.status_code == 404

                                                 
    res_patch = await client.patch(f"/events/{active_event_id}/tables/{table_id}", json={"name": "Hacked Name"}, headers=headers_attacker)
    assert res_patch.status_code == 404

                                                     
    res_delete = await client.delete(f"/events/{active_event_id}/tables/{table_id}", headers=headers_attacker)
    assert res_delete.status_code == 404

@pytest.mark.asyncio
async def test_manipulating_table_with_wrong_event_id_returns_404(
    client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict
):
    headers = {"Authorization": f"Bearer {owner_token}"}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    table_id = create_res.json()["id"]

    wrong_event_id = uuid.uuid4()

                                                                                                                              
    res_get = await client.get(f"/events/{wrong_event_id}/tables/{table_id}", headers=headers)
    assert res_get.status_code == 404

    res_patch = await client.patch(f"/events/{wrong_event_id}/tables/{table_id}", json={"name": "New Name"}, headers=headers)
    assert res_patch.status_code == 404

@pytest.mark.asyncio
async def test_unassign_non_existent_guest_returns_404(client: AsyncClient, owner_token: str, active_event_id: uuid.UUID, valid_table_payload: dict):
    headers = {"Authorization": f"Bearer {owner_token}"}
    create_res = await client.post(f"/events/{active_event_id}/tables/", json=valid_table_payload, headers=headers)
    table_id = create_res.json()["id"]

    random_guest_id = uuid.uuid4()
    
                                                         
    response = await client.delete(f"/events/{active_event_id}/tables/{table_id}/guests/{random_guest_id}", headers=headers)
    assert response.status_code == 404