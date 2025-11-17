"""Integration tests for order management."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consumer import Consumer
from app.models.link import Link, LinkStatus
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.supplier import Supplier


@pytest.mark.asyncio
async def test_create_order_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can create an order."""
    # Setup consumer
    consumer_data = {
        "email": "consumer1@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 1")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Setup supplier
    supplier_data = {
        "email": "supplier1@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 1", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create accepted link
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create products
    product1 = Product(
        supplier_id=supplier.id,
        name="Product 1",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="PROD-001",
        stock_qty=10,
        is_active=True,
    )
    product2 = Product(
        supplier_id=supplier.id,
        name="Product 2",
        price_kzt=Decimal("2000.00"),
        currency="KZT",
        sku="PROD-002",
        stock_qty=5,
        is_active=True,
    )
    db_session.add(product1)
    db_session.add(product2)
    await db_session.commit()
    await db_session.refresh(product1)
    await db_session.refresh(product2)

    # Create order
    order_data = {
        "supplier_id": supplier.id,
        "items": [
            {"product_id": product1.id, "qty": 2},
            {"product_id": product2.id, "qty": 1},
        ],
    }

    response = await client.post(
        "/api/v1/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["supplier_id"] == supplier.id
    assert data["consumer_id"] == consumer.id
    assert data["status"] == OrderStatus.PENDING.value
    assert len(data["items"]) == 2
    # Total should be: 1000 * 2 + 2000 * 1 = 4000
    assert data["total_kzt"] == "4000.00"


@pytest.mark.asyncio
async def test_create_order_negative_qty_blocked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that negative quantity is blocked."""
    # Setup consumer and supplier
    consumer_data = {
        "email": "consumer2@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 2")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier2@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 2", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create accepted link
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create product
    product = Product(
        supplier_id=supplier.id,
        name="Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="PROD-003",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Try to create order with negative quantity (should fail validation)
    order_data = {
        "supplier_id": supplier.id,
        "items": [{"product_id": product.id, "qty": -1}],
    }

    response = await client.post(
        "/api/v1/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_order_zero_qty_blocked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that zero quantity is blocked."""
    # Setup (similar to above)
    consumer_data = {
        "email": "consumer3@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 3")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier3@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 3", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create accepted link
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create product
    product = Product(
        supplier_id=supplier.id,
        name="Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="PROD-004",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Try to create order with zero quantity (should fail validation)
    order_data = {
        "supplier_id": supplier.id,
        "items": [{"product_id": product.id, "qty": 0}],
    }

    response = await client.post(
        "/api/v1/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_order_without_accepted_link_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer without accepted link cannot create order."""
    # Setup consumer
    consumer_data = {
        "email": "consumer4@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 4")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Setup supplier
    supplier_data = {
        "email": "supplier4@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 4", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create product
    product = Product(
        supplier_id=supplier.id,
        name="Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="PROD-005",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Try to create order without link (should fail)
    order_data = {
        "supplier_id": supplier.id,
        "items": [{"product_id": product.id, "qty": 1}],
    }

    response = await client.post(
        "/api/v1/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_order_status_pending_to_accepted(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: pending -> accepted."""
    # Setup consumer and supplier
    consumer_data = {
        "email": "consumer5@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 5")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier5@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 5", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Update status to accepted
    status_update = {"status": OrderStatus.ACCEPTED.value}

    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == OrderStatus.ACCEPTED.value


@pytest.mark.asyncio
async def test_update_order_status_pending_to_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: pending -> rejected."""
    # Setup (similar to above)
    consumer_data = {
        "email": "consumer6@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 6")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier6@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 6", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Update status to rejected
    status_update = {"status": OrderStatus.REJECTED.value}

    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == OrderStatus.REJECTED.value


@pytest.mark.asyncio
async def test_update_order_status_accepted_to_in_progress(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: accepted -> in_progress."""
    # Setup
    consumer_data = {
        "email": "consumer7@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 7")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier7@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 7", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order with accepted status
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.ACCEPTED,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Update status to in_progress
    status_update = {"status": OrderStatus.IN_PROGRESS.value}

    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == OrderStatus.IN_PROGRESS.value


@pytest.mark.asyncio
async def test_update_order_status_in_progress_to_completed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: in_progress -> completed."""
    # Setup
    consumer_data = {
        "email": "consumer8@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 8")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier8@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 8", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order with in_progress status
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.IN_PROGRESS,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Update status to completed
    status_update = {"status": OrderStatus.COMPLETED.value}

    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == OrderStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_update_order_status_invalid_transition_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that invalid state transitions are rejected."""
    # Setup
    consumer_data = {
        "email": "consumer9@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 9")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier9@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 9", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order with rejected status (cannot be changed)
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.REJECTED,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Try to update rejected order (should fail)
    status_update = {"status": OrderStatus.ACCEPTED.value}

    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 400
    assert "Cannot transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_order_as_consumer_own_order(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can view their own orders."""
    # Setup
    consumer_data = {
        "email": "consumer10@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 10")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier10@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 10", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Get order as consumer
    response = await client.get(
        f"/api/v1/orders/{order.id}",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order.id
    assert data["consumer_id"] == consumer.id


@pytest.mark.asyncio
async def test_get_order_as_supplier_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier owner can view their supplier's orders."""
    # Setup
    consumer_data = {
        "email": "consumer11@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 11")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier11@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 11", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create order
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=Decimal("1000.00"),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Get order as supplier owner
    response = await client.get(
        f"/api/v1/orders/{order.id}",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order.id
    assert data["supplier_id"] == supplier.id


@pytest.mark.asyncio
async def test_get_orders_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can list their own orders."""
    # Setup
    consumer_data = {
        "email": "consumer12@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 12")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Create multiple suppliers and orders
    for i in range(3):
        supplier_data = {
            "email": f"supplier12_{i}@example.com",
            "password": "password123",
            "role": "supplier_owner",
        }
        supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
        supplier_token = supplier_response.json()["access_token"]

        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {supplier_token}"},
        )
        supplier_user_id = me_response.json()["id"]

        supplier = Supplier(
            user_id=supplier_user_id, company_name=f"Supplier 12_{i}", is_active=True
        )
        db_session.add(supplier)
        await db_session.commit()
        await db_session.refresh(supplier)

        order = Order(
            supplier_id=supplier.id,
            consumer_id=consumer.id,
            status=OrderStatus.PENDING,
            total_kzt=Decimal("1000.00"),
        )
        db_session.add(order)
    await db_session.commit()

    # Get orders
    response = await client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert all(item["consumer_id"] == consumer.id for item in data["items"])


@pytest.mark.asyncio
async def test_get_orders_as_supplier_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier owner can list their supplier's orders."""
    # Setup supplier
    supplier_data = {
        "email": "supplier13@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 13", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create multiple consumers and orders
    for i in range(3):
        consumer_data = {
            "email": f"consumer13_{i}@example.com",
            "password": "password123",
            "role": "consumer",
        }
        consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
        consumer_token = consumer_response.json()["access_token"]

        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {consumer_token}"},
        )
        consumer_user_id = me_response.json()["id"]

        consumer = Consumer(
            user_id=consumer_user_id, organization_name=f"Consumer 13_{i}"
        )
        db_session.add(consumer)
        await db_session.commit()
        await db_session.refresh(consumer)

        order = Order(
            supplier_id=supplier.id,
            consumer_id=consumer.id,
            status=OrderStatus.PENDING,
            total_kzt=Decimal("1000.00"),
        )
        db_session.add(order)
    await db_session.commit()

    # Get orders
    response = await client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert all(item["supplier_id"] == supplier.id for item in data["items"])


@pytest.mark.asyncio
async def test_get_orders_with_status_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test status filtering for orders."""
    # Setup
    consumer_data = {
        "email": "consumer14@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 14")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier14@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 14", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create orders with different statuses
    order1 = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=Decimal("1000.00"),
    )
    order2 = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.ACCEPTED,
        total_kzt=Decimal("2000.00"),
    )
    db_session.add(order1)
    db_session.add(order2)
    await db_session.commit()

    # Filter by pending status
    response = await client.get(
        "/api/v1/orders?status=pending",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == OrderStatus.PENDING.value for item in data["items"])


@pytest.mark.asyncio
async def test_create_order_with_inactive_product_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that inactive products cannot be ordered."""
    # Setup
    consumer_data = {
        "email": "consumer15@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 15")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier15@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    supplier = Supplier(
        user_id=supplier_user_id, company_name="Supplier 15", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create accepted link
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create inactive product
    product = Product(
        supplier_id=supplier.id,
        name="Inactive Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="INACT-001",
        stock_qty=10,
        is_active=False,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Try to create order with inactive product (should fail)
    order_data = {
        "supplier_id": supplier.id,
        "items": [{"product_id": product.id, "qty": 1}],
    }

    response = await client.post(
        "/api/v1/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 400
    assert "not active" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_order_with_wrong_supplier_product_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that products from different supplier cannot be ordered."""
    # Setup consumer
    consumer_data = {
        "email": "consumer16@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 16")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Setup supplier 1
    supplier1_data = {
        "email": "supplier16_1@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier1_response = await client.post("/api/v1/auth/signup", json=supplier1_data)
    supplier1_token = supplier1_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier1_token}"},
    )
    supplier1_user_id = me_response.json()["id"]

    supplier1 = Supplier(
        user_id=supplier1_user_id, company_name="Supplier 16_1", is_active=True
    )
    db_session.add(supplier1)
    await db_session.commit()
    await db_session.refresh(supplier1)

    # Setup supplier 2
    supplier2_data = {
        "email": "supplier16_2@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier2_response = await client.post("/api/v1/auth/signup", json=supplier2_data)
    supplier2_token = supplier2_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier2_token}"},
    )
    supplier2_user_id = me_response.json()["id"]

    supplier2 = Supplier(
        user_id=supplier2_user_id, company_name="Supplier 16_2", is_active=True
    )
    db_session.add(supplier2)
    await db_session.commit()
    await db_session.refresh(supplier2)

    # Create accepted link with supplier 1
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier1.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create product for supplier 2
    product = Product(
        supplier_id=supplier2.id,
        name="Supplier 2 Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="SUP2-001",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Try to create order with supplier 1 but product from supplier 2 (should fail)
    order_data = {
        "supplier_id": supplier1.id,
        "items": [{"product_id": product.id, "qty": 1}],
    }

    response = await client.post(
        "/api/v1/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"].lower()
