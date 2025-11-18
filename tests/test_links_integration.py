"""Integration tests for link management."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consumer.model import Consumer
from app.modules.link.model import Link, LinkStatus
from app.modules.supplier.model import Supplier


@pytest.mark.asyncio
async def test_create_link_request_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can create a link request."""
    # Create consumer user
    consumer_data = {
        "email": "consumer1@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    assert consumer_response.status_code == 201
    consumer_token = consumer_response.json()["access_token"]
    consumer_user_id = consumer_response.json()["access_token"]  # We'll get from /me

    # Get consumer user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    # Create consumer profile
    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer Org")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Create supplier user
    supplier_data = {
        "email": "supplier1@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    assert supplier_response.status_code == 201
    supplier_token = supplier_response.json()["access_token"]

    # Get supplier user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )
    supplier_user_id = me_response.json()["id"]

    # Create supplier profile
    supplier = Supplier(
        user_id=supplier_user_id, company_name="Test Supplier Co", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create link request
    link_request = {"supplier_id": supplier.id}

    response = await client.post(
        "/api/v1/links/requests",
        json=link_request,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consumer_id"] == consumer.id
    assert data["supplier_id"] == supplier.id
    assert data["status"] == LinkStatus.PENDING.value


@pytest.mark.asyncio
async def test_create_link_request_duplicate_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that duplicate link request fails."""
    # Create consumer
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

    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer 2")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Create supplier
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
        user_id=supplier_user_id, company_name="Test Supplier 2", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create first link request
    link_request = {"supplier_id": supplier.id}
    response1 = await client.post(
        "/api/v1/links/requests",
        json=link_request,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await client.post(
        "/api/v1/links/requests",
        json=link_request,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_create_link_request_as_non_consumer_fails(client: AsyncClient) -> None:
    """Test that non-consumer cannot create link request."""
    # Create supplier owner
    supplier_data = {
        "email": "supplier3@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    # Try to create link request as supplier owner
    link_request = {"supplier_id": 1}

    response = await client.post(
        "/api/v1/links/requests",
        json=link_request,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_link_status_pending_to_accepted(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: pending -> accepted."""
    # Setup: Create consumer and supplier
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

    # Create link request
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.PENDING
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Update status to accepted
    status_update = {"status": LinkStatus.ACCEPTED.value}

    response = await client.patch(
        f"/api/v1/links/{link.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == LinkStatus.ACCEPTED.value


@pytest.mark.asyncio
async def test_update_link_status_pending_to_denied(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: pending -> denied."""
    # Similar setup to above
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

    # Create link request
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.PENDING
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Update status to denied
    status_update = {"status": LinkStatus.DENIED.value}

    response = await client.patch(
        f"/api/v1/links/{link.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == LinkStatus.DENIED.value


@pytest.mark.asyncio
async def test_update_link_status_accepted_to_blocked(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: accepted -> blocked."""
    # Setup
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

    # Create link with accepted status
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.ACCEPTED
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Update status to blocked
    status_update = {"status": LinkStatus.BLOCKED.value}

    response = await client.patch(
        f"/api/v1/links/{link.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == LinkStatus.BLOCKED.value


@pytest.mark.asyncio
async def test_update_link_status_denied_to_pending(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test state machine: denied -> pending."""
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

    # Create link with denied status
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.DENIED
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Update status to pending
    status_update = {"status": LinkStatus.PENDING.value}

    response = await client.patch(
        f"/api/v1/links/{link.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == LinkStatus.PENDING.value


@pytest.mark.asyncio
async def test_update_link_status_invalid_transition_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that invalid state transitions are rejected."""
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

    # Create link with blocked status (cannot be changed)
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.BLOCKED
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Try to update blocked link (should fail)
    status_update = {"status": LinkStatus.ACCEPTED.value}

    response = await client.patch(
        f"/api/v1/links/{link.id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 400
    assert "Cannot transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_link_as_consumer_own_link(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can view their own links."""
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

    # Create link
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.PENDING
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Get link as consumer
    response = await client.get(
        f"/api/v1/links/{link.id}",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == link.id
    assert data["consumer_id"] == consumer.id


@pytest.mark.asyncio
async def test_get_link_as_supplier_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that supplier owner can view their supplier's links."""
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

    # Create link
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.PENDING
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Get link as supplier owner
    response = await client.get(
        f"/api/v1/links/{link.id}",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == link.id
    assert data["supplier_id"] == supplier.id


@pytest.mark.asyncio
async def test_get_link_unauthorized_access_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that unauthorized users cannot view links."""
    # Setup consumer and supplier
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

    # Create another consumer
    other_consumer_data = {
        "email": "otherconsumer@example.com",
        "password": "password123",
        "role": "consumer",
    }
    other_consumer_response = await client.post(
        "/api/v1/auth/signup", json=other_consumer_data
    )
    other_consumer_token = other_consumer_response.json()["access_token"]

    # Create link between first consumer and supplier
    link = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.PENDING
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    # Try to get link as other consumer (should fail)
    response = await client.get(
        f"/api/v1/links/{link.id}",
        headers={"Authorization": f"Bearer {other_consumer_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_consumer_links_with_pagination(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test pagination for consumer links."""
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

    # Create supplier
    supplier_data = {
        "email": "supplier12@example.com",
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
        user_id=supplier_user_id, company_name="Supplier 12", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create multiple suppliers and links (to avoid unique constraint violation)
    links: list[Link] = []
    for i in range(5):
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

        new_supplier = Supplier(
            user_id=supplier_user_id, company_name=f"Supplier 12_{i}", is_active=True
        )
        db_session.add(new_supplier)
        await db_session.commit()
        await db_session.refresh(new_supplier)

        link = Link(
            consumer_id=consumer.id,
            supplier_id=new_supplier.id,
            status=LinkStatus.PENDING,
        )
        links.append(link)
        db_session.add(link)
    await db_session.commit()

    # Get links with pagination
    response = await client.get(
        "/api/v1/links?page=1&size=2",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "size" in data
    assert "total" in data
    assert "pages" in data
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) <= 2


@pytest.mark.asyncio
async def test_get_consumer_links_with_status_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test status filtering for consumer links."""
    # Setup
    consumer_data = {
        "email": "consumer13@example.com",
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

    consumer = Consumer(user_id=consumer_user_id, organization_name="Consumer 13")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

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

    # Create another supplier for second link
    supplier2_data = {
        "email": "supplier13_2@example.com",
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
        user_id=supplier2_user_id, company_name="Supplier 13_2", is_active=True
    )
    db_session.add(supplier2)
    await db_session.commit()
    await db_session.refresh(supplier2)

    # Create links with different statuses
    link1 = Link(
        consumer_id=consumer.id, supplier_id=supplier.id, status=LinkStatus.PENDING
    )
    link2 = Link(
        consumer_id=consumer.id, supplier_id=supplier2.id, status=LinkStatus.ACCEPTED
    )
    db_session.add(link1)
    db_session.add(link2)
    await db_session.commit()

    # Filter by pending status
    response = await client.get(
        "/api/v1/links?status=pending",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == LinkStatus.PENDING.value for item in data["items"])


@pytest.mark.asyncio
async def test_get_incoming_links_with_pagination(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test pagination for incoming links."""
    # Setup supplier
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

    # Wait a moment for the supplier to be fully committed
    await db_session.refresh(supplier)

    # Create multiple consumers and links
    for i in range(5):
        consumer_data = {
            "email": f"consumer14_{i}@example.com",
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
            user_id=consumer_user_id, organization_name=f"Consumer 14_{i}"
        )
        db_session.add(consumer)
        await db_session.commit()
        await db_session.refresh(consumer)

        link = Link(
            consumer_id=consumer.id,
            supplier_id=supplier.id,
            status=LinkStatus.PENDING,
        )
        db_session.add(link)
    await db_session.commit()

    # Get incoming links with pagination
    response = await client.get(
        "/api/v1/links/incoming?page=1&size=2",
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "size" in data
    assert "total" in data
    assert "pages" in data
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) <= 2
