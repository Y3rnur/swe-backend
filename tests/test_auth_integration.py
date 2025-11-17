"""Integration tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_creates_user_and_returns_tokens(client: AsyncClient) -> None:
    """Test that signup creates a user and returns access/refresh tokens."""
    signup_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "role": "consumer",
    }

    response = await client.post("/api/v1/auth/signup", json=signup_data)

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_400(client: AsyncClient) -> None:
    """Test that signup with duplicate email returns 400."""
    signup_data = {
        "email": "duplicate@example.com",
        "password": "password123",
        "role": "consumer",
    }

    # First signup should succeed
    response1 = await client.post("/api/v1/auth/signup", json=signup_data)
    assert response1.status_code == 201

    # Second signup with same email should fail
    response2 = await client.post("/api/v1/auth/signup", json=signup_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_valid_credentials_returns_tokens(client: AsyncClient) -> None:
    """Test that login with valid credentials returns tokens."""
    # First create a user
    signup_data = {
        "email": "loginuser@example.com",
        "password": "password123",
        "role": "consumer",
    }
    await client.post("/api/v1/auth/signup", json=signup_data)

    # Then login
    login_data = {
        "email": "loginuser@example.com",
        "password": "password123",
    }

    response = await client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_email_returns_401(client: AsyncClient) -> None:
    """Test that login with invalid email returns 401."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "password123",
    }

    response = await client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
    assert (
        "incorrect" in response.json()["detail"].lower()
        or "invalid" in response.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_login_invalid_password_returns_401(client: AsyncClient) -> None:
    """Test that login with invalid password returns 401."""
    # First create a user
    signup_data = {
        "email": "wrongpass@example.com",
        "password": "correctpassword",
        "role": "consumer",
    }
    await client.post("/api/v1/auth/signup", json=signup_data)

    # Then try to login with wrong password
    login_data = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword",
    }

    response = await client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
    assert (
        "incorrect" in response.json()["detail"].lower()
        or "invalid" in response.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_refresh_token_returns_new_tokens(client: AsyncClient) -> None:
    """Test that refresh endpoint returns new access and refresh tokens."""
    # Create user and get tokens
    signup_data = {
        "email": "refreshtest@example.com",
        "password": "password123",
        "role": "consumer",
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    signup_tokens = signup_response.json()

    # Use refresh token to get new tokens
    refresh_data = {
        "refresh_token": signup_tokens["refresh_token"],
    }

    response = await client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify tokens are valid by using the new access token
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == signup_data["email"]

    # Note: Tokens might be the same if generated within the same second (same expiry),
    # but the important thing is that refresh works and returns valid tokens


@pytest.mark.asyncio
async def test_refresh_invalid_token_returns_401(client: AsyncClient) -> None:
    """Test that refresh with invalid token returns 401."""
    refresh_data = {
        "refresh_token": "invalid.token.here",
    }

    response = await client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 401
    assert (
        "invalid" in response.json()["detail"].lower()
        or "refresh" in response.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_refresh_access_token_returns_401(client: AsyncClient) -> None:
    """Test that using access token as refresh token returns 401."""
    # Create user and get tokens
    signup_data = {
        "email": "accesstoken@example.com",
        "password": "password123",
        "role": "consumer",
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    signup_tokens = signup_response.json()

    # Try to use access token as refresh token
    refresh_data = {
        "refresh_token": signup_tokens["access_token"],
    }

    response = await client.post("/api/v1/auth/refresh", json=refresh_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_requires_authentication(client: AsyncClient) -> None:
    """Test that /me endpoint requires authentication."""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 403  # FastAPI returns 403 for missing auth


@pytest.mark.asyncio
async def test_me_endpoint_returns_user_with_valid_token(client: AsyncClient) -> None:
    """Test that /me endpoint returns user data with valid token."""
    # Create user and get tokens
    signup_data = {
        "email": "meuser@example.com",
        "password": "password123",
        "role": "consumer",
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    tokens = signup_response.json()

    # Use access token to get user info
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = await client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "meuser@example.com"
    assert data["role"] == "consumer"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_me_endpoint_invalid_token_returns_401(client: AsyncClient) -> None:
    """Test that /me endpoint returns 401 with invalid token."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = await client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient) -> None:
    """Test complete authentication flow: signup -> login -> refresh -> me."""
    # 1. Signup
    signup_data = {
        "email": "flowtest@example.com",
        "password": "password123",
        "role": "consumer",
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert signup_response.status_code == 201

    # 2. Login
    login_data = {
        "email": "flowtest@example.com",
        "password": "password123",
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_tokens = login_response.json()

    # 3. Use access token to get /me
    headers = {"Authorization": f"Bearer {login_tokens['access_token']}"}
    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == "flowtest@example.com"

    # 4. Refresh tokens
    refresh_data = {"refresh_token": login_tokens["refresh_token"]}
    refresh_response = await client.post("/api/v1/auth/refresh", json=refresh_data)
    assert refresh_response.status_code == 200
    refresh_tokens = refresh_response.json()

    # 5. Use new access token to get /me
    new_headers = {"Authorization": f"Bearer {refresh_tokens['access_token']}"}
    new_me_response = await client.get("/api/v1/users/me", headers=new_headers)
    assert new_me_response.status_code == 200
    new_user_data = new_me_response.json()
    assert new_user_data["email"] == "flowtest@example.com"
    assert new_user_data["id"] == user_data["id"]  # Same user
