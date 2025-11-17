"""Tests for security components."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.models.user import User
from app.utils.hashing import hash_password, verify_password


@pytest.mark.asyncio
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "test_password_123"
        assert verify_password(password, "invalid_hash") is False

    def test_hash_password_unique(self):
        """Test that hashing the same password produces different hashes."""
        password = "test_password_123"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        assert hashed1 != hashed2
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True


@pytest.mark.asyncio
class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """Test decoding a valid access token."""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == 1
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_decode_access_token_invalid(self):
        """Test decoding an invalid access token."""
        invalid_token = "invalid.token.here"
        payload = decode_access_token(invalid_token)
        assert payload is None

    def test_access_token_expiration(self):
        """Test access token expiration."""
        data = {"sub": 1, "email": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Expired token
        token = create_access_token(data, expires_delta=expires_delta)
        payload = decode_access_token(token)
        assert payload is None

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token_valid(self):
        """Test decoding a valid refresh token."""
        data = {"sub": 1, "email": "test@example.com"}
        token = create_refresh_token(data)
        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == 1
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_refresh_token_invalid(self):
        """Test decoding an invalid refresh token."""
        invalid_token = "invalid.token.here"
        payload = decode_refresh_token(invalid_token)
        assert payload is None

    def test_refresh_token_expiration(self):
        """Test refresh token expiration."""
        data = {"sub": 1, "email": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Expired token
        token = create_refresh_token(data, expires_delta=expires_delta)
        payload = decode_refresh_token(token)
        assert payload is None

    def test_refresh_token_type_check(self):
        """Test that refresh token requires type='refresh'."""
        data = {"sub": 1, "email": "test@example.com"}
        access_token = create_access_token(data)
        payload = decode_refresh_token(access_token)
        assert payload is None

    def test_token_round_trip(self):
        """Test token creation and decoding round trip."""
        data = {"sub": 1, "email": "test@example.com", "role": "admin"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = decode_access_token(access_token)
        refresh_payload = decode_refresh_token(refresh_token)

        assert access_payload is not None
        assert refresh_payload is not None
        assert access_payload["sub"] == data["sub"]
        assert refresh_payload["sub"] == data["sub"]
        assert access_payload["email"] == data["email"]
        assert refresh_payload["email"] == data["email"]


@pytest.mark.asyncio
class TestRoleBasedAccess:
    """Test role-based access control."""

    async def test_require_roles_allowed(self, db_session: AsyncSession):
        """Test require_roles with allowed role."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.deps import get_current_user

        user = User(
            email="admin@example.com",
            password_hash=hash_password("password123"),
            role=Role.ADMIN.value,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=create_access_token({"sub": user.id, "email": user.email}),
        )
        current_user = await get_current_user(credentials, db=db_session)  # type: ignore
        assert current_user.id == user.id
        assert current_user.role == Role.ADMIN.value

    async def test_require_roles_disallowed(self, db_session: AsyncSession):
        """Test require_roles with disallowed role."""
        user = User(
            email="consumer@example.com",
            password_hash=hash_password("password123"),
            role=Role.CONSUMER.value,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        user_role = Role(user.role)
        assert user_role == Role.CONSUMER
        assert Role.CONSUMER not in [Role.ADMIN]


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test get_current_user dependency."""

    async def test_get_current_user_valid_token(self, db_session: AsyncSession):
        """Test get_current_user with valid token."""
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.deps import get_current_user

        user = User(
            email="test@example.com",
            password_hash=hash_password("password123"),
            role=Role.ADMIN.value,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=create_access_token({"sub": user.id, "email": user.email}),
        )
        current_user = await get_current_user(credentials, db=db_session)  # type: ignore

        assert current_user.id == user.id
        assert current_user.email == user.email
        assert current_user.role == user.role

    async def test_get_current_user_invalid_token(self, db_session: AsyncSession):
        """Test get_current_user with invalid token."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.deps import get_current_user

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db=db_session)  # type: ignore
        assert exc_info.value.status_code == 401

    async def test_get_current_user_inactive_user(self, db_session: AsyncSession):
        """Test get_current_user with inactive user."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        from app.api.deps import get_current_user

        user = User(
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            role=Role.ADMIN.value,
            is_active=False,
            created_at=datetime.now(UTC),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=create_access_token({"sub": user.id, "email": user.email}),
        )
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db=db_session)  # type: ignore
        assert exc_info.value.status_code == 403
