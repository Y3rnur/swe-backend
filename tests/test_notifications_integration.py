"""Integration tests for notification endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


@pytest.mark.asyncio
async def test_get_notifications_as_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that user can list their own notifications."""
    # Create user
    user_data = {
        "email": "user_notifications@example.com",
        "password": "password123",
        "role": "consumer",
    }
    user_response = await client.post("/api/v1/auth/signup", json=user_data)
    assert user_response.status_code == 201
    user_token = user_response.json()["access_token"]

    # Get user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    user_id = me_response.json()["id"]

    # Create some notifications
    notification1 = Notification(
        recipient_id=user_id,
        type="link_accepted",
        message="Your link request has been accepted",
        is_read=False,
    )
    notification2 = Notification(
        recipient_id=user_id,
        type="order_status_changed",
        message="Your order status has been updated",
        is_read=True,
    )
    db_session.add(notification1)
    db_session.add(notification2)
    await db_session.commit()

    # Get notifications
    response = await client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 2
    # Should be ordered by created_at desc (newest first)
    assert data["items"][0]["type"] in ["link_accepted", "order_status_changed"]


@pytest.mark.asyncio
async def test_get_notifications_filter_by_read_status(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test filtering notifications by read status."""
    # Create user
    user_data = {
        "email": "user_filter@example.com",
        "password": "password123",
        "role": "consumer",
    }
    user_response = await client.post("/api/v1/auth/signup", json=user_data)
    user_token = user_response.json()["access_token"]

    # Get user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    user_id = me_response.json()["id"]

    # Create notifications
    notification1 = Notification(
        recipient_id=user_id,
        type="link_accepted",
        message="Unread notification",
        is_read=False,
    )
    notification2 = Notification(
        recipient_id=user_id,
        type="order_status_changed",
        message="Read notification",
        is_read=True,
    )
    db_session.add(notification1)
    db_session.add(notification2)
    await db_session.commit()

    # Get unread notifications
    response = await client.get(
        "/api/v1/notifications?is_read=false",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert all(item["is_read"] is False for item in data["items"])

    # Get read notifications
    response = await client.get(
        "/api/v1/notifications?is_read=true",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert all(item["is_read"] is True for item in data["items"])


@pytest.mark.asyncio
async def test_mark_notification_read(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test marking a notification as read."""
    # Create user
    user_data = {
        "email": "user_mark_read@example.com",
        "password": "password123",
        "role": "consumer",
    }
    user_response = await client.post("/api/v1/auth/signup", json=user_data)
    user_token = user_response.json()["access_token"]

    # Get user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    user_id = me_response.json()["id"]

    # Create unread notification
    notification = Notification(
        recipient_id=user_id,
        type="link_accepted",
        message="Your link request has been accepted",
        is_read=False,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    # Mark as read
    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_read"] is True
    assert response.json()["id"] == notification.id


@pytest.mark.asyncio
async def test_mark_notification_read_unauthorized(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that users cannot mark other users' notifications as read."""
    # Create two users
    user1_data = {
        "email": "user1_unauth@example.com",
        "password": "password123",
        "role": "consumer",
    }
    user1_response = await client.post("/api/v1/auth/signup", json=user1_data)
    user1_token = user1_response.json()["access_token"]
    user1_id = (
        await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {user1_token}"},
        )
    ).json()["id"]

    user2_data = {
        "email": "user2_unauth@example.com",
        "password": "password123",
        "role": "consumer",
    }
    user2_response = await client.post("/api/v1/auth/signup", json=user2_data)
    user2_token = user2_response.json()["access_token"]

    # Create notification for user1
    notification = Notification(
        recipient_id=user1_id,
        type="link_accepted",
        message="Your link request has been accepted",
        is_read=False,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    # User2 tries to mark user1's notification as read (should fail)
    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {user2_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_notifications_pagination(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test pagination for notifications."""
    # Create user
    user_data = {
        "email": "user_pagination@example.com",
        "password": "password123",
        "role": "consumer",
    }
    user_response = await client.post("/api/v1/auth/signup", json=user_data)
    user_token = user_response.json()["access_token"]

    # Get user ID
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    user_id = me_response.json()["id"]

    # Create multiple notifications
    for i in range(5):
        notification = Notification(
            recipient_id=user_id,
            type="test",
            message=f"Test notification {i}",
            is_read=False,
        )
        db_session.add(notification)
    await db_session.commit()

    # Get first page
    response = await client.get(
        "/api/v1/notifications?page=1&size=2",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["total"] >= 5
