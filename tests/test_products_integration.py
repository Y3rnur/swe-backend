"""Integration tests for product management and catalog."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consumer import Consumer
from app.models.link import Link, LinkStatus
from app.models.product import Product
from app.models.supplier import Supplier


@pytest.mark.asyncio
async def test_create_product_as_supplier_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier owner can create a product."""
    # Create supplier owner
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

    # Create product
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price_kzt": "1000.00",
        "currency": "KZT",
        "sku": "TEST-001",
        "stock_qty": 10,
        "is_active": True,
    }

    response = await client.post(
        "/api/v1/products",
        json=product_data,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["supplier_id"] == supplier.id
    assert data["sku"] == product_data["sku"]


@pytest.mark.asyncio
async def test_create_product_as_non_supplier_fails(client: AsyncClient) -> None:
    """Test that non-supplier cannot create products."""
    # Create consumer
    consumer_data = {
        "email": "consumer1@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    product_data = {
        "name": "Test Product",
        "price_kzt": "1000.00",
        "sku": "TEST-001",
    }

    response = await client.post(
        "/api/v1/products",
        json=product_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_product_as_supplier_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier owner can update their product."""
    # Setup supplier
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

    # Create product
    product = Product(
        supplier_id=supplier.id,
        name="Original Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="ORIG-001",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Update product
    update_data = {
        "name": "Updated Product",
        "price_kzt": "1500.00",
    }

    response = await client.put(
        f"/api/v1/products/{product.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product"
    assert data["price_kzt"] == "1500.00"


@pytest.mark.asyncio
async def test_update_product_unauthorized_supplier_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier cannot update another supplier's product."""
    # Create supplier 1
    supplier1_data = {
        "email": "supplier3@example.com",
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
        user_id=supplier1_user_id, company_name="Supplier 3", is_active=True
    )
    db_session.add(supplier1)
    await db_session.commit()
    await db_session.refresh(supplier1)

    # Create product for supplier 1
    product = Product(
        supplier_id=supplier1.id,
        name="Supplier 1 Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="SUP1-001",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Create supplier 2
    supplier2_data = {
        "email": "supplier4@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier2_response = await client.post("/api/v1/auth/signup", json=supplier2_data)
    supplier2_token = supplier2_response.json()["access_token"]

    # Try to update supplier 1's product as supplier 2
    update_data = {"name": "Hacked Product"}

    response = await client.put(
        f"/api/v1/products/{product.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {supplier2_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_product_as_supplier_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier owner can delete their product."""
    # Setup supplier
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

    # Create product
    product = Product(
        supplier_id=supplier.id,
        name="Product to Delete",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="DEL-001",
        stock_qty=10,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    # Delete product
    response = await client.delete(
        f"/api/v1/products/{product.id}",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 204

    # Verify product is deleted
    response = await client.get(
        f"/api/v1/products?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    data = response.json()
    assert product.id not in [item["id"] for item in data["items"]]


@pytest.mark.asyncio
async def test_get_products_with_supplier_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test getting products filtered by supplier_id."""
    # Setup supplier
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

    # Create products
    for i in range(3):
        product = Product(
            supplier_id=supplier.id,
            name=f"Product {i}",
            price_kzt=Decimal("1000.00"),
            currency="KZT",
            sku=f"PROD-{i:03d}",
            stock_qty=10,
            is_active=True,
        )
        db_session.add(product)
    await db_session.commit()

    # Get products
    response = await client.get(
        f"/api/v1/products?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert all(item["supplier_id"] == supplier.id for item in data["items"])


@pytest.mark.asyncio
async def test_get_catalog_with_accepted_link(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer with accepted link can view catalog."""
    # Setup consumer
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

    # Setup supplier
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

    # Create accepted link
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create products
    for i in range(2):
        product = Product(
            supplier_id=supplier.id,
            name=f"Catalog Product {i}",
            price_kzt=Decimal("1000.00"),
            currency="KZT",
            sku=f"CAT-{i:03d}",
            stock_qty=10,
            is_active=True,
        )
        db_session.add(product)
    await db_session.commit()

    # Get catalog
    response = await client.get(
        f"/api/v1/catalog?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert all(item["supplier_id"] == supplier.id for item in data["items"])


@pytest.mark.asyncio
async def test_get_catalog_without_accepted_link_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer without accepted link cannot view catalog."""
    # Setup consumer
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

    # Setup supplier
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

    # Create pending link (not accepted)
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.PENDING,
    )
    db_session.add(link)
    await db_session.commit()

    # Try to get catalog (should fail)
    response = await client.get(
        f"/api/v1/catalog?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 403
    assert "accepted link" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_catalog_with_no_link_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer with no link cannot view catalog."""
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

    # Try to get catalog without any link (should fail)
    response = await client.get(
        f"/api/v1/catalog?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_catalog_as_non_consumer_fails(client: AsyncClient) -> None:
    """Test that non-consumer cannot access catalog endpoint."""
    # Create supplier
    supplier_data = {
        "email": "supplier10@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    # Try to get catalog as supplier (should fail)
    response = await client.get(
        "/api/v1/catalog?supplier_id=1",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_catalog_only_shows_active_products(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that catalog only shows active products."""
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

    # Create accepted link
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()

    # Create active and inactive products
    active_product = Product(
        supplier_id=supplier.id,
        name="Active Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="ACT-001",
        stock_qty=10,
        is_active=True,
    )
    inactive_product = Product(
        supplier_id=supplier.id,
        name="Inactive Product",
        price_kzt=Decimal("1000.00"),
        currency="KZT",
        sku="INACT-001",
        stock_qty=10,
        is_active=False,
    )
    db_session.add(active_product)
    db_session.add(inactive_product)
    await db_session.commit()

    # Get catalog
    response = await client.get(
        f"/api/v1/catalog?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == active_product.id
    assert data["items"][0]["is_active"] is True
