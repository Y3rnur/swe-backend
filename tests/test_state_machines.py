"""Tests for state machine transitions (order, link, complaint status)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_status_transition_pending_to_accepted(
    client: AsyncClient,
    order,
    auth_headers_supplier_owner: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Test order status transition from PENDING to ACCEPTED."""
    # Update order status
    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "accepted"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_status_transition_pending_to_rejected(
    client: AsyncClient,
    order,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test order status transition from PENDING to REJECTED."""
    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "rejected"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_status_transition_accepted_to_in_progress(
    client: AsyncClient,
    order,
    auth_headers_supplier_owner: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Test order status transition from ACCEPTED to IN_PROGRESS."""
    # First accept the order
    await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "accepted"},
        headers=auth_headers_supplier_owner,
    )

    # Then move to in_progress
    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "in_progress"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_status_transition_invalid_from_rejected(
    client: AsyncClient,
    order,
    auth_headers_supplier_owner: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Test that rejected orders cannot be changed."""
    # Reject the order
    await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "rejected"},
        headers=auth_headers_supplier_owner,
    )

    # Try to change from rejected (should fail)
    response = await client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "accepted"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_link_status_transition_pending_to_accepted(
    client: AsyncClient,
    pending_link,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test link status transition from PENDING to ACCEPTED."""
    response = await client.patch(
        f"/api/v1/links/{pending_link.id}/status",
        json={"status": "accepted"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_link_status_transition_pending_to_denied(
    client: AsyncClient,
    pending_link,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test link status transition from PENDING to DENIED."""
    response = await client.patch(
        f"/api/v1/links/{pending_link.id}/status",
        json={"status": "denied"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "denied"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_link_status_transition_accepted_to_blocked(
    client: AsyncClient,
    accepted_link,
    auth_headers_supplier_owner: dict[str, str],
) -> None:
    """Test link status transition from ACCEPTED to BLOCKED."""
    response = await client.patch(
        f"/api/v1/links/{accepted_link.id}/status",
        json={"status": "blocked"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "blocked"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_link_status_transition_denied_to_pending(
    client: AsyncClient,
    pending_link,
    auth_headers_supplier_owner: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Test link status transition from DENIED to PENDING (re-request)."""
    # First deny
    await client.patch(
        f"/api/v1/links/{pending_link.id}/status",
        json={"status": "denied"},
        headers=auth_headers_supplier_owner,
    )

    # Then can go back to pending
    response = await client.patch(
        f"/api/v1/links/{pending_link.id}/status",
        json={"status": "pending"},
        headers=auth_headers_supplier_owner,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complaint_status_transition_open_to_escalated(
    client: AsyncClient,
    complaint,
    auth_headers_supplier_sales: dict[str, str],
) -> None:
    """Test complaint status transition from OPEN to ESCALATED."""
    response = await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={"status": "escalated"},
        headers=auth_headers_supplier_sales,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "escalated"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complaint_status_transition_open_to_resolved(
    client: AsyncClient,
    complaint,
    auth_headers_supplier_manager: dict[str, str],
) -> None:
    """Test complaint status transition from OPEN to RESOLVED with resolution."""
    response = await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={
            "status": "resolved",
            "resolution": "Issue has been resolved",
        },
        headers=auth_headers_supplier_manager,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["resolution"] == "Issue has been resolved"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complaint_status_transition_resolved_requires_resolution(
    client: AsyncClient,
    complaint,
    auth_headers_supplier_manager: dict[str, str],
) -> None:
    """Test that resolving a complaint requires resolution text."""
    response = await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={"status": "resolved"},
        headers=auth_headers_supplier_manager,
    )
    assert response.status_code == 400
    assert "resolution" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complaint_status_transition_resolved_cannot_change(
    client: AsyncClient,
    complaint,
    auth_headers_supplier_manager: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Test that resolved complaints cannot be changed."""
    # First resolve
    await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={
            "status": "resolved",
            "resolution": "Resolved",
        },
        headers=auth_headers_supplier_manager,
    )

    # Try to change (should fail)
    response = await client.patch(
        f"/api/v1/complaints/{complaint.id}/status",
        json={"status": "open"},
        headers=auth_headers_supplier_manager,
    )
    assert response.status_code == 400
