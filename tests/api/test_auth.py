"""Integration tests for authentication endpoints."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.utils.hashing import hash_password


class TestSignup:
    """Test signup endpoint."""

    async def test_signup_success(self, client: AsyncClient):
        """Test successful user signup."""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "role": "consumer",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_signup_duplicate_email(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test signup with duplicate email."""
        user = User(
            email="existing@example.com",
            password_hash=hash_password("password123"),
            role=Role.CONSUMER.value,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "existing@example.com",
                "password": "newpassword123",
                "role": "consumer",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_signup_invalid_email(self, client: AsyncClient):
        """Test signup with invalid email."""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "invalid-email",
                "password": "testpassword123",
                "role": "consumer",
            },
        )
        assert response.status_code == 422

    async def test_signup_short_password(self, client: AsyncClient):
        """Test signup with short password."""
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "password": "short",
                "role": "consumer",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Test login endpoint."""

    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login."""
        password = "testpassword123"
        user = User(
            email="login@example.com",
            password_hash=hash_password(password),
            role=Role.CONSUMER.value,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_invalid_password(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with incorrect password."""
        user = User(
            email="wrongpass@example.com",
            password_hash=hash_password("correctpassword"),
            role=Role.CONSUMER.value,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with inactive user."""
        password = "password123"
        user = User(
            email="inactive@example.com",
            password_hash=hash_password(password),
            role=Role.CONSUMER.value,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": password,
            },
        )
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestRefresh:
    """Test refresh token endpoint."""

    async def test_refresh_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful token refresh."""
        user = User(
            email="refresh@example.com",
            password_hash=hash_password("password123"),
            role=Role.CONSUMER.value,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        refresh_token = create_refresh_token(data={"sub": user.id})
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_refresh_access_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh with access token (should fail)."""
        user = User(
            email="accesstoken@example.com",
            password_hash=hash_password("password123"),
            role=Role.CONSUMER.value,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        access_token = create_access_token(data={"sub": user.id})
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401

    async def test_refresh_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh with inactive user."""
        user = User(
            email="inactiverf@example.com",
            password_hash=hash_password("password123"),
            role=Role.CONSUMER.value,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        refresh_token = create_refresh_token(data={"sub": user.id})
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401


class TestGetMe:
    """Test get current user endpoint."""

    async def test_get_me_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful get current user."""
        user = User(
            email="me@example.com",
            password_hash=hash_password("password123"),
            role=Role.ADMIN.value,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["role"] == user.role
        assert data["is_active"] == user.is_active

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test get current user without token."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test get current user with invalid token."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    async def test_get_me_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test get current user with inactive account."""
        user = User(
            email="inactiveme@example.com",
            password_hash=hash_password("password123"),
            role=Role.CONSUMER.value,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()
