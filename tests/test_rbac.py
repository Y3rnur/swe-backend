"""Role-based access control tests."""

import pytest
from fastapi import HTTPException, status

from app.api.deps import require_roles
from app.core.roles import Role
from app.models.user import User


class TestRequireRoles:
    """Tests for require_roles dependency."""

    @pytest.mark.asyncio
    async def test_require_roles_allows_matching_role(self):
        """Test that require_roles allows access for matching role."""
        # Create a mock user with ADMIN role
        mock_user = User(
            id=1,
            email="admin@example.com",
            password_hash="hash",
            role=Role.ADMIN.value,
            is_active=True,
        )

        # Create role checker for ADMIN
        role_checker = require_roles(Role.ADMIN)

        # Should not raise exception
        result = await role_checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_roles_allows_multiple_roles(self):
        """Test that require_roles allows access if user has one of the required roles."""
        # Create a mock user with CONSUMER role
        mock_user = User(
            id=1,
            email="consumer@example.com",
            password_hash="hash",
            role=Role.CONSUMER.value,
            is_active=True,
        )

        # Create role checker for CONSUMER or ADMIN
        role_checker = require_roles(Role.CONSUMER, Role.ADMIN)

        # Should not raise exception
        result = await role_checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_roles_returns_403_for_disallowed_role(self):
        """Test that require_roles returns 403 for disallowed role."""
        # Create a mock user with CONSUMER role
        mock_user = User(
            id=1,
            email="consumer@example.com",
            password_hash="hash",
            role=Role.CONSUMER.value,
            is_active=True,
        )

        # Create role checker for ADMIN only
        role_checker = require_roles(Role.ADMIN)

        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_roles_returns_403_for_invalid_role(self):
        """Test that require_roles returns 403 for invalid role string."""
        # Create a mock user with invalid role
        mock_user = User(
            id=1,
            email="user@example.com",
            password_hash="hash",
            role="invalid_role",
            is_active=True,
        )

        # Create role checker for ADMIN
        role_checker = require_roles(Role.ADMIN)

        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_roles_allows_supplier_roles(self):
        """Test that require_roles works with supplier roles."""
        # Test SUPPLIER_OWNER
        owner_user = User(
            id=1,
            email="owner@example.com",
            password_hash="hash",
            role=Role.SUPPLIER_OWNER.value,
            is_active=True,
        )
        role_checker = require_roles(Role.SUPPLIER_OWNER)
        result = await role_checker(current_user=owner_user)
        assert result == owner_user

        # Test SUPPLIER_MANAGER
        manager_user = User(
            id=2,
            email="manager@example.com",
            password_hash="hash",
            role=Role.SUPPLIER_MANAGER.value,
            is_active=True,
        )
        role_checker = require_roles(Role.SUPPLIER_MANAGER)
        result = await role_checker(current_user=manager_user)
        assert result == manager_user

        # Test SUPPLIER_SALES
        sales_user = User(
            id=3,
            email="sales@example.com",
            password_hash="hash",
            role=Role.SUPPLIER_SALES.value,
            is_active=True,
        )
        role_checker = require_roles(Role.SUPPLIER_SALES)
        result = await role_checker(current_user=sales_user)
        assert result == sales_user

    @pytest.mark.asyncio
    async def test_require_roles_403_for_wrong_supplier_role(self):
        """Test that require_roles returns 403 when supplier role doesn't match."""
        # User is SUPPLIER_SALES but endpoint requires SUPPLIER_OWNER
        sales_user = User(
            id=1,
            email="sales@example.com",
            password_hash="hash",
            role=Role.SUPPLIER_SALES.value,
            is_active=True,
        )

        role_checker = require_roles(Role.SUPPLIER_OWNER)

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=sales_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
