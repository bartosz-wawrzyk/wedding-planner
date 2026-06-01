import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.auth.models import User, RefreshToken, UserRole
from app.core.security import hash_token
from datetime import datetime, timezone, timedelta

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": "register_success@example.com",
        "password": "strongpassword123"
    })
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/auth/register", json=payload)
    
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    email = "login_success@example.com"
    password = "secret_password"
    await client.post("/auth/register", json={"email": email, "password": password})

    response = await client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "user"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_rotation_success(client: AsyncClient):
    email = "refresh_flow@example.com"
    password = "password123"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    
    old_refresh_token = login_res.json()["refresh_token"]

    refresh_res = await client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert refresh_res.status_code == 200
    
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["refresh_token"] != old_refresh_token

    reuse_res = await client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert reuse_res.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_expired(client: AsyncClient, db_session: AsyncSession):
    user = User(email="expired_token@example.com", hashed_password="fakehashpassword", role=UserRole.USER)
    db_session.add(user)
    await db_session.commit()

    expired_token_raw = "some_mock_expired_token_value_xyz"
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(expired_token_raw),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db_session.add(db_token)
    await db_session.commit()

    response = await client.post("/auth/refresh", json={"refresh_token": expired_token_raw})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_protected_route(client: AsyncClient):
    email = "me_protected@example.com"
    password = "password123"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_inactive_user_access_blocked(client: AsyncClient, db_session: AsyncSession):
    email = "banned@example.com"
    password = "password123"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_active = False
    await db_session.commit()

    headers = {"Authorization": f"Bearer {token}"}
    response_me = await client.get("/auth/me", headers=headers)
    assert response_me.status_code == 403

    response_refresh = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response_refresh.status_code == 403
    
@pytest.mark.asyncio
async def test_cannot_refresh_token_if_user_was_banned_mid_session(client: AsyncClient, db_session: AsyncSession):
    """SECURITY: A banned user cannot use their refresh token."""
    email = "active_then_banned@example.com"
    password = "Password123!"
                                                   
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    refresh_token = login_res.json()["refresh_token"]
                                                                         
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_active = False
    await db_session.commit()

                                                                   
    refresh_res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
                                                                           
    assert refresh_res.status_code == 403
    assert refresh_res.json()["detail"] == "Konto jest nieaktywne"


@pytest.mark.asyncio
async def test_refresh_token_rotation_invalidates_old_token_immediately(client: AsyncClient):
    """VULNERABILITY TEST (Replay Attack): Once a refresh token has been used, it becomes invalid."""
    email = "rotation_test@example.com"
    password = "Password123!"
    
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    first_refresh_token = login_res.json()["refresh_token"]
                                                    
    success_refresh = await client.post("/auth/refresh", json={"refresh_token": first_refresh_token})
    assert success_refresh.status_code == 200
                                                                       
    malicious_refresh = await client.post("/auth/refresh", json={"refresh_token": first_refresh_token})
                                                        
    assert malicious_refresh.status_code == 401


@pytest.mark.asyncio
async def test_expired_tokens_are_cleaned_from_db(client: AsyncClient, db_session: AsyncSession):
    """OPTIMIZATION TEST: Expired tokens are removed without cluttering the database on Render.com."""
    email = "cleanup_test@example.com"
    password = "Password123!"
    
    await client.post("/auth/register", json={"email": email, "password": password})
    login_res = await client.post("/auth/login", json={"email": email, "password": password})
    refresh_token = login_res.json()["refresh_token"]
                                          
    tokens_count_pre = await db_session.execute(select(RefreshToken))
    assert len(tokens_count_pre.scalars().all()) == 1
                                                                        
    await client.post("/auth/refresh", json={"refresh_token": refresh_token})
                                                                                                                      
    tokens_count_post = await db_session.execute(select(RefreshToken))
    assert len(tokens_count_post.scalars().all()) == 1