"""Tests for access rules and RBAC permissions."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_cannot_create_product(
    client: AsyncClient,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer cannot create products."""
    response = await client.post(
        "/api/v1/products",
        json={
            "name": "Test Product",
            "price_kzt": "10000.00",
            "currency": "KZT",
            "sku": "TEST-001",
            "stock_qty": 100,
        },
        headers=auth_headers_consumer,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_owner_can_create_product(
    client: AsyncClient,
    supplier,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test that supplier owner can create products."""
    response = await client.post(
        "/api/v1/products",
        json={
            "name": "New Product",
            "price_kzt": "15000.00",
            "currency": "KZT",
            "sku": "NEW-001",
            "stock_qty": 50,
        },
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "New Product"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_manager_can_create_product(
    client: AsyncClient,
    auth_headers_supplier_manager: dict[str, str],
) -> None:
    """Test that supplier manager can create products."""
    response = await client.post(
        "/api/v1/products",
        json={
            "name": "Manager Product",
            "price_kzt": "12000.00",
            "currency": "KZT",
            "sku": "MGR-001",
            "stock_qty": 75,
        },
        headers=auth_headers_supplier_manager,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_sales_cannot_create_product(
    client: AsyncClient,
    auth_headers_supplier_sales: dict[str, str],
) -> None:
    """Test that supplier sales cannot create products."""
    response = await client.post(
        "/api/v1/products",
        json={
            "name": "Sales Product",
            "price_kzt": "10000.00",
            "currency": "KZT",
            "sku": "SALES-001",
            "stock_qty": 100,
        },
        headers=auth_headers_supplier_sales,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_can_only_see_own_orders(
    client: AsyncClient,
    order,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer can only see their own orders."""
    response = await client.get(
        f"/api/v1/orders/{order.id}",
        headers=auth_headers_consumer,
    )
    assert response.status_code == 200
    assert response.json()["id"] == order.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_owner_can_see_supplier_orders(
    client: AsyncClient,
    order,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test that supplier owner can see their supplier's orders."""
    response = await client.get(
        f"/api/v1/orders/{order.id}",
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_cannot_update_order_status(
    client: AsyncClient,
    order,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer cannot update order status."""
    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "accepted"},
        headers=auth_headers_consumer,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_owner_can_update_order_status(
    client: AsyncClient,
    order,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test that supplier owner can update order status."""
    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "accepted"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_can_create_link_request(
    client: AsyncClient,
    supplier,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer can create link requests."""
    response = await client.post(
        "/api/v1/links/requests",
        json={"supplier_id": supplier.id},
        headers=auth_headers_consumer,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_owner_cannot_create_link_request(
    client: AsyncClient,
    supplier,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test that supplier owner cannot create link requests."""
    response = await client.post(
        "/api/v1/links/requests",
        json={"supplier_id": supplier.id},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_owner_can_update_link_status(
    client: AsyncClient,
    accepted_link,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test that supplier owner can update link status."""
    response = await client.patch(
        f"/api/v1/links/{accepted_link.id}/status",
        json={"status": "blocked"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_cannot_update_link_status(
    client: AsyncClient,
    accepted_link,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer cannot update link status."""
    response = await client.patch(
        f"/api/v1/links/{accepted_link.id}/status",
        json={"status": "blocked"},
        headers=auth_headers_consumer,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_can_create_complaint(
    client: AsyncClient,
    order,
    supplier_sales_user,
    supplier_manager_user,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer can create complaints."""
    response = await client.post(
        "/api/v1/complaints",
        json={
            "order_id": order.id,
            "sales_rep_id": supplier_sales_user.id,
            "manager_id": supplier_manager_user.id,
            "description": "Test complaint",
        },
        headers=auth_headers_consumer,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.integration
async def test_supplier_sales_can_update_complaint_status(
    client: AsyncClient,
    complaint,
    auth_headers_supplier_sales: dict[str, str],
) -> None:
    """Test that supplier sales can update complaint status."""
    response = await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={"status": "escalated"},
        headers=auth_headers_supplier_sales,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_consumer_cannot_update_complaint_status(
    client: AsyncClient,
    complaint,
    auth_headers_consumer: dict[str, str],
) -> None:
    """Test that consumer cannot update complaint status."""
    response = await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={"status": "escalated"},
        headers=auth_headers_consumer,
    )
    assert response.status_code == 403
