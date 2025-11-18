"""Integration tests for chat endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consumer.model import Consumer
from app.modules.order.model import Order, OrderStatus
from app.modules.supplier.model import Supplier, SupplierStaff


@pytest.mark.asyncio
async def test_create_chat_session_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can create a chat session."""
    # Create consumer user
    consumer_data = {
        "email": "consumer_chat@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    assert consumer_response.status_code == 201
    consumer_token = consumer_response.json()["access_token"]

    # Get consumer user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]

    # Create consumer profile
    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Create supplier owner user
    supplier_data = {
        "email": "supplier_chat@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    assert supplier_response.status_code == 201
    supplier_user_id = supplier_response.json()["access_token"]  # Will get from /me

    # Get supplier user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {supplier_response.json()['access_token']}"},
    )
    supplier_user_id = me_response.json()["id"]

    # Create supplier profile
    supplier = Supplier(
        user_id=supplier_user_id, company_name="Test Supplier", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    # Create sales rep user
    sales_rep_data = {
        "email": "salesrep@example.com",
        "password": "password123",
        "role": "supplier_sales",
    }
    sales_rep_response = await client.post("/api/v1/auth/signup", json=sales_rep_data)
    assert sales_rep_response.status_code == 201
    sales_rep_token = sales_rep_response.json()["access_token"]

    # Get sales rep user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {sales_rep_token}"},
    )
    sales_rep_user_id = me_response.json()["id"]

    # Create supplier staff (sales rep)
    staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(staff)
    await db_session.commit()

    # Create chat session
    session_data = {"sales_rep_id": sales_rep_user_id}

    response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consumer_id"] == consumer.id
    assert data["sales_rep_id"] == sales_rep_user_id
    assert data["order_id"] is None


@pytest.mark.asyncio
async def test_create_chat_session_with_order(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can create a chat session linked to an order."""
    # Create consumer user
    consumer_data = {
        "email": "consumer_order_chat@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    assert consumer_response.status_code == 201
    consumer_token = consumer_response.json()["access_token"]

    # Get consumer user ID and create profile
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]
    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    # Create supplier and sales rep (similar setup as above)
    supplier_data = {
        "email": "supplier_order_chat@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {supplier_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    supplier = Supplier(
        user_id=supplier_user_id, company_name="Test Supplier", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    sales_rep_data = {
        "email": "salesrep_order@example.com",
        "password": "password123",
        "role": "supplier_sales",
    }
    sales_rep_response = await client.post("/api/v1/auth/signup", json=sales_rep_data)
    sales_rep_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {sales_rep_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(staff)
    await db_session.commit()

    # Create an order
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=1000.00,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create chat session with order
    session_data = {"sales_rep_id": sales_rep_user_id, "order_id": order.id}

    response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order.id


@pytest.mark.asyncio
async def test_create_chat_session_as_non_consumer_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that non-consumers cannot create chat sessions."""
    # Create supplier owner user
    supplier_data = {
        "email": "supplier_nochat@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    # Try to create chat session
    session_data = {"sales_rep_id": 1}

    response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_chat_session_invalid_sales_rep_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that creating a chat session with invalid sales rep fails."""
    # Create consumer user
    consumer_data = {
        "email": "consumer_invalid@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    # Get consumer user ID and create profile
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    consumer_user_id = me_response.json()["id"]
    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer")
    db_session.add(consumer)
    await db_session.commit()

    # Try to create chat session with non-existent sales rep
    session_data = {"sales_rep_id": 99999}

    response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 404

    # Try to create chat session with user who is not a sales rep
    regular_user_data = {
        "email": "regular@example.com",
        "password": "password123",
        "role": "consumer",
    }
    regular_response = await client.post("/api/v1/auth/signup", json=regular_user_data)
    regular_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {regular_response.json()['access_token']}"
            },
        )
    ).json()["id"]

    session_data = {"sales_rep_id": regular_user_id}

    response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_chat_sessions_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can list their own chat sessions."""
    # Setup: Create consumer, supplier, sales rep, and chat session
    consumer_data = {
        "email": "consumer_list@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]
    consumer_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {consumer_token}"},
        )
    ).json()["id"]
    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier_list@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {supplier_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    supplier = Supplier(
        user_id=supplier_user_id, company_name="Test Supplier", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    sales_rep_data = {
        "email": "salesrep_list@example.com",
        "password": "password123",
        "role": "supplier_sales",
    }
    sales_rep_response = await client.post("/api/v1/auth/signup", json=sales_rep_data)
    sales_rep_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {sales_rep_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(staff)
    await db_session.commit()

    # Create chat session via API
    session_data = {"sales_rep_id": sales_rep_user_id}
    create_response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert create_response.status_code == 201

    # List sessions
    response = await client.get(
        "/api/v1/chats/sessions",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["consumer_id"] == consumer.id


@pytest.mark.asyncio
async def test_create_and_get_chat_messages(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test creating and retrieving chat messages."""
    # Setup: Create consumer, supplier, sales rep, and chat session
    consumer_data = {
        "email": "consumer_msg@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]
    consumer_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {consumer_token}"},
        )
    ).json()["id"]
    consumer = Consumer(user_id=consumer_user_id, organization_name="Test Consumer")
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)

    supplier_data = {
        "email": "supplier_msg@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {supplier_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    supplier = Supplier(
        user_id=supplier_user_id, company_name="Test Supplier", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    sales_rep_data = {
        "email": "salesrep_msg@example.com",
        "password": "password123",
        "role": "supplier_sales",
    }
    sales_rep_response = await client.post("/api/v1/auth/signup", json=sales_rep_data)
    sales_rep_token = sales_rep_response.json()["access_token"]
    sales_rep_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {sales_rep_token}"},
        )
    ).json()["id"]
    staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(staff)
    await db_session.commit()

    # Create chat session
    session_data = {"sales_rep_id": sales_rep_user_id}
    create_response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    # Consumer sends a message
    message_data = {"text": "Hello, I have a question"}
    msg_response = await client.post(
        f"/api/v1/chats/sessions/{session_id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert msg_response.status_code == 201
    assert msg_response.json()["text"] == "Hello, I have a question"
    assert msg_response.json()["sender_id"] == consumer_user_id

    # Sales rep sends a message
    message_data = {"text": "How can I help you?"}
    msg_response = await client.post(
        f"/api/v1/chats/sessions/{session_id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {sales_rep_token}"},
    )
    assert msg_response.status_code == 201

    # Get messages as consumer
    messages_response = await client.get(
        f"/api/v1/chats/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert messages_response.status_code == 200
    data = messages_response.json()
    assert "items" in data
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_non_participant_cannot_access_messages(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that non-participants cannot access chat messages."""
    # Setup: Create two consumers, supplier, sales rep, and chat session
    consumer1_data = {
        "email": "consumer1_private@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer1_response = await client.post("/api/v1/auth/signup", json=consumer1_data)
    consumer1_token = consumer1_response.json()["access_token"]
    consumer1_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {consumer1_token}"},
        )
    ).json()["id"]
    consumer1 = Consumer(user_id=consumer1_user_id, organization_name="Consumer 1")
    db_session.add(consumer1)
    await db_session.commit()
    await db_session.refresh(consumer1)

    consumer2_data = {
        "email": "consumer2_private@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer2_response = await client.post("/api/v1/auth/signup", json=consumer2_data)
    consumer2_token = consumer2_response.json()["access_token"]

    supplier_data = {
        "email": "supplier_private@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {supplier_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    supplier = Supplier(
        user_id=supplier_user_id, company_name="Test Supplier", is_active=True
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)

    sales_rep_data = {
        "email": "salesrep_private@example.com",
        "password": "password123",
        "role": "supplier_sales",
    }
    sales_rep_response = await client.post("/api/v1/auth/signup", json=sales_rep_data)
    sales_rep_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {sales_rep_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(staff)
    await db_session.commit()

    # Consumer 1 creates a chat session
    session_data = {"sales_rep_id": sales_rep_user_id}
    create_response = await client.post(
        "/api/v1/chats/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {consumer1_token}"},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    # Consumer 2 tries to access the session messages (should fail)
    messages_response = await client.get(
        f"/api/v1/chats/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {consumer2_token}"},
    )
    assert messages_response.status_code == 403

    # Consumer 2 tries to send a message (should fail)
    message_data = {"text": "Unauthorized message"}
    msg_response = await client.post(
        f"/api/v1/chats/sessions/{session_id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {consumer2_token}"},
    )
    assert msg_response.status_code == 403
