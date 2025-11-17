"""Integration tests for complaint endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import ComplaintStatus
from app.models.consumer import Consumer
from app.models.order import Order, OrderStatus
from app.models.supplier import Supplier
from app.models.supplier_staff import SupplierStaff


@pytest.mark.asyncio
async def test_create_complaint_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can create a complaint."""
    # Create consumer user
    consumer_data = {
        "email": "consumer_complaint@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    assert consumer_response.status_code == 201
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

    # Create supplier owner
    supplier_data = {
        "email": "supplier_complaint@example.com",
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

    # Create sales rep
    sales_rep_data = {
        "email": "salesrep_complaint@example.com",
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
    sales_rep_staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(sales_rep_staff)
    await db_session.commit()

    # Create manager
    manager_data = {
        "email": "manager_complaint@example.com",
        "password": "password123",
        "role": "supplier_manager",
    }
    manager_response = await client.post("/api/v1/auth/signup", json=manager_data)
    manager_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {manager_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    manager_staff = SupplierStaff(
        user_id=manager_user_id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(manager_staff)
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

    # Create complaint
    complaint_data = {
        "order_id": order.id,
        "sales_rep_id": sales_rep_user_id,
        "manager_id": manager_user_id,
        "description": "Order was delayed",
    }

    response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order.id
    assert data["consumer_id"] == consumer.id
    assert data["sales_rep_id"] == sales_rep_user_id
    assert data["manager_id"] == manager_user_id
    assert data["status"] == ComplaintStatus.OPEN.value
    assert data["description"] == "Order was delayed"
    assert data["resolution"] is None


@pytest.mark.asyncio
async def test_create_complaint_as_non_consumer_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that non-consumers cannot create complaints."""
    supplier_data = {
        "email": "supplier_nocomplaint@example.com",
        "password": "password123",
        "role": "supplier_owner",
    }
    supplier_response = await client.post("/api/v1/auth/signup", json=supplier_data)
    supplier_token = supplier_response.json()["access_token"]

    complaint_data = {
        "order_id": 1,
        "sales_rep_id": 1,
        "manager_id": 1,
        "description": "Test complaint",
    }

    response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {supplier_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_complaint_invalid_order_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that creating a complaint with invalid order fails."""
    consumer_data = {
        "email": "consumer_invalid_order@example.com",
        "password": "password123",
        "role": "consumer",
    }
    consumer_response = await client.post("/api/v1/auth/signup", json=consumer_data)
    consumer_token = consumer_response.json()["access_token"]

    complaint_data = {
        "order_id": 99999,
        "sales_rep_id": 1,
        "manager_id": 1,
        "description": "Test complaint",
    }

    response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_complaint_status_open_to_escalated(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that sales rep can escalate a complaint."""
    # Setup: Create consumer, supplier, sales rep, manager, order, and complaint
    consumer_data = {
        "email": "consumer_escalate@example.com",
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
        "email": "supplier_escalate@example.com",
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
        "email": "salesrep_escalate@example.com",
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
    sales_rep_staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(sales_rep_staff)
    await db_session.commit()

    manager_data = {
        "email": "manager_escalate@example.com",
        "password": "password123",
        "role": "supplier_manager",
    }
    manager_response = await client.post("/api/v1/auth/signup", json=manager_data)
    manager_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {manager_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    manager_staff = SupplierStaff(
        user_id=manager_user_id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(manager_staff)
    await db_session.commit()

    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=1000.00,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create complaint
    complaint_data = {
        "order_id": order.id,
        "sales_rep_id": sales_rep_user_id,
        "manager_id": manager_user_id,
        "description": "Order issue",
    }
    create_response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    assert create_response.status_code == 201
    complaint_id = create_response.json()["id"]

    # Sales rep escalates complaint
    status_update = {"status": ComplaintStatus.ESCALATED.value}

    response = await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {sales_rep_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == ComplaintStatus.ESCALATED.value


@pytest.mark.asyncio
async def test_update_complaint_status_escalated_to_resolved(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that manager can resolve an escalated complaint."""
    # Similar setup as above, but escalate first, then resolve
    consumer_data = {
        "email": "consumer_resolve@example.com",
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
        "email": "supplier_resolve@example.com",
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
        "email": "salesrep_resolve@example.com",
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
    sales_rep_staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(sales_rep_staff)
    await db_session.commit()

    manager_data = {
        "email": "manager_resolve@example.com",
        "password": "password123",
        "role": "supplier_manager",
    }
    manager_response = await client.post("/api/v1/auth/signup", json=manager_data)
    manager_token = manager_response.json()["access_token"]
    manager_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
    ).json()["id"]
    manager_staff = SupplierStaff(
        user_id=manager_user_id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(manager_staff)
    await db_session.commit()

    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=1000.00,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create complaint
    complaint_data = {
        "order_id": order.id,
        "sales_rep_id": sales_rep_user_id,
        "manager_id": manager_user_id,
        "description": "Order issue",
    }
    create_response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    complaint_id = create_response.json()["id"]

    # Escalate first
    status_update = {"status": ComplaintStatus.ESCALATED.value}
    await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={
            "Authorization": f"Bearer {sales_rep_response.json()['access_token']}"
        },
    )

    # Manager resolves
    status_update = {
        "status": ComplaintStatus.RESOLVED.value,
        "resolution": "Issue has been resolved",
    }

    response = await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == ComplaintStatus.RESOLVED.value
    assert response.json()["resolution"] == "Issue has been resolved"


@pytest.mark.asyncio
async def test_update_complaint_status_invalid_transition_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that invalid status transitions are rejected."""
    # Setup similar to above
    consumer_data = {
        "email": "consumer_invalid@example.com",
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
        "email": "supplier_invalid@example.com",
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
        "email": "salesrep_invalid@example.com",
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
    sales_rep_staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(sales_rep_staff)
    await db_session.commit()

    manager_data = {
        "email": "manager_invalid@example.com",
        "password": "password123",
        "role": "supplier_manager",
    }
    manager_response = await client.post("/api/v1/auth/signup", json=manager_data)
    manager_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {manager_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    manager_staff = SupplierStaff(
        user_id=manager_user_id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(manager_staff)
    await db_session.commit()

    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=1000.00,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create complaint
    complaint_data = {
        "order_id": order.id,
        "sales_rep_id": sales_rep_user_id,
        "manager_id": manager_user_id,
        "description": "Order issue",
    }
    create_response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    complaint_id = create_response.json()["id"]

    # First escalate the complaint
    status_update = {"status": ComplaintStatus.ESCALATED.value}
    escalate_response = await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {sales_rep_token}"},
    )
    assert escalate_response.status_code == 200

    # Get manager token
    manager_token = manager_response.json()["access_token"]

    # Resolve the complaint
    status_update = {
        "status": ComplaintStatus.RESOLVED.value,
        "resolution": "Issue resolved",
    }
    resolve_response = await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resolve_response.status_code == 200

    # Now try invalid transition: resolved -> escalated (should fail)
    status_update = {"status": ComplaintStatus.ESCALATED.value}

    response = await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {sales_rep_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_resolve_complaint_requires_resolution_text(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that resolving a complaint requires resolution text."""
    # Setup similar to above
    consumer_data = {
        "email": "consumer_resolution@example.com",
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
        "email": "supplier_resolution@example.com",
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
        "email": "salesrep_resolution@example.com",
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
    sales_rep_staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(sales_rep_staff)
    await db_session.commit()

    manager_data = {
        "email": "manager_resolution@example.com",
        "password": "password123",
        "role": "supplier_manager",
    }
    manager_response = await client.post("/api/v1/auth/signup", json=manager_data)
    manager_token = manager_response.json()["access_token"]
    manager_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
    ).json()["id"]
    manager_staff = SupplierStaff(
        user_id=manager_user_id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(manager_staff)
    await db_session.commit()

    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=1000.00,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create complaint
    complaint_data = {
        "order_id": order.id,
        "sales_rep_id": sales_rep_user_id,
        "manager_id": manager_user_id,
        "description": "Order issue",
    }
    create_response = await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )
    complaint_id = create_response.json()["id"]

    # Try to resolve without resolution text (should fail)
    status_update = {"status": ComplaintStatus.RESOLVED.value}

    response = await client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json=status_update,
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_complaints_as_consumer(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that consumer can list their own complaints."""
    # Setup and create complaint (similar to above)
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
    sales_rep_staff = SupplierStaff(
        user_id=sales_rep_user_id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(sales_rep_staff)
    await db_session.commit()

    manager_data = {
        "email": "manager_list@example.com",
        "password": "password123",
        "role": "supplier_manager",
    }
    manager_response = await client.post("/api/v1/auth/signup", json=manager_data)
    manager_user_id = (
        await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {manager_response.json()['access_token']}"
            },
        )
    ).json()["id"]
    manager_staff = SupplierStaff(
        user_id=manager_user_id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(manager_staff)
    await db_session.commit()

    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=1000.00,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Create complaint
    complaint_data = {
        "order_id": order.id,
        "sales_rep_id": sales_rep_user_id,
        "manager_id": manager_user_id,
        "description": "Order issue",
    }
    await client.post(
        "/api/v1/complaints",
        json=complaint_data,
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    # List complaints
    response = await client.get(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {consumer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["consumer_id"] == consumer.id
