"""Comprehensive test fixtures for users, roles, and sample data."""

from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
from app.modules.chat.model import ChatSession
from app.modules.complaint.model import Complaint, ComplaintStatus
from app.modules.consumer.model import Consumer
from app.modules.link.model import Link, LinkStatus
from app.modules.notification.model import Notification
from app.modules.order.model import Order, OrderItem, OrderStatus
from app.modules.product.model import Product
from app.modules.supplier.model import Supplier, SupplierStaff
from app.modules.user.model import User
from app.utils.hashing import hash_password


@pytest.fixture
async def consumer_user(db_session: AsyncSession) -> AsyncGenerator[User]:
    """Create a consumer user for testing."""
    user = User(
        email="consumer@test.com",
        password_hash=hash_password("Password123"),
        role=Role.CONSUMER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def consumer(
    consumer_user: User, db_session: AsyncSession
) -> AsyncGenerator[Consumer]:
    """Create a consumer profile for testing."""
    consumer = Consumer(
        user_id=consumer_user.id,
        organization_name="Test Consumer Org",
    )
    db_session.add(consumer)
    await db_session.commit()
    await db_session.refresh(consumer)
    return consumer


@pytest.fixture
async def supplier_owner_user(db_session: AsyncSession) -> AsyncGenerator[User]:
    """Create a supplier owner user for testing."""
    user = User(
        email="supplier.owner@test.com",
        password_hash=hash_password("Password123"),
        role=Role.SUPPLIER_OWNER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def supplier(
    supplier_owner_user: User, db_session: AsyncSession
) -> AsyncGenerator[Supplier]:
    """Create a supplier for testing."""
    supplier = Supplier(
        user_id=supplier_owner_user.id,
        company_name="Test Supplier Co",
        is_active=True,
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


@pytest.fixture
async def supplier_manager_user(db_session: AsyncSession) -> AsyncGenerator[User]:
    """Create a supplier manager user for testing."""
    user = User(
        email="supplier.manager@test.com",
        password_hash=hash_password("Password123"),
        role=Role.SUPPLIER_MANAGER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def supplier_manager_staff(
    supplier_manager_user: User,
    supplier: Supplier,
    db_session: AsyncSession,
) -> AsyncGenerator[SupplierStaff]:
    """Create a supplier manager staff member for testing."""
    staff = SupplierStaff(
        user_id=supplier_manager_user.id,
        supplier_id=supplier.id,
        staff_role="manager",
    )
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)
    return staff


@pytest.fixture
async def supplier_sales_user(db_session: AsyncSession) -> AsyncGenerator[User]:
    """Create a supplier sales user for testing."""
    user = User(
        email="supplier.sales@test.com",
        password_hash=hash_password("Password123"),
        role=Role.SUPPLIER_SALES.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def supplier_sales_staff(
    supplier_sales_user: User,
    supplier: Supplier,
    db_session: AsyncSession,
) -> AsyncGenerator[SupplierStaff]:
    """Create a supplier sales staff member for testing."""
    staff = SupplierStaff(
        user_id=supplier_sales_user.id,
        supplier_id=supplier.id,
        staff_role="sales",
    )
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)
    return staff


@pytest.fixture
async def product(
    supplier: Supplier, db_session: AsyncSession
) -> AsyncGenerator[Product]:
    """Create a product for testing."""
    product = Product(
        supplier_id=supplier.id,
        name="Test Product",
        description="Test product description",
        price_kzt=Decimal("10000.00"),
        currency="KZT",
        sku="TEST-001",
        stock_qty=100,
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def accepted_link(
    consumer: Consumer,
    supplier: Supplier,
    db_session: AsyncSession,
) -> AsyncGenerator[Link]:
    """Create an accepted link between consumer and supplier."""
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.ACCEPTED,
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)
    return link


@pytest.fixture
async def pending_link(
    consumer: Consumer,
    supplier: Supplier,
    db_session: AsyncSession,
) -> AsyncGenerator[Link]:
    """Create a pending link between consumer and supplier."""
    link = Link(
        consumer_id=consumer.id,
        supplier_id=supplier.id,
        status=LinkStatus.PENDING,
    )
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)
    return link


@pytest.fixture
async def order(
    consumer: Consumer,
    supplier: Supplier,
    product: Product,
    accepted_link: Link,
    db_session: AsyncSession,
) -> AsyncGenerator[Order]:
    """Create an order with items for testing."""
    order = Order(
        supplier_id=supplier.id,
        consumer_id=consumer.id,
        status=OrderStatus.PENDING,
        total_kzt=Decimal("20000.00"),
    )
    db_session.add(order)
    await db_session.flush()

    # Add order items
    item1 = OrderItem(
        order_id=order.id,
        product_id=product.id,
        qty=2,
        unit_price_kzt=product.price_kzt,
    )
    db_session.add(item1)

    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.fixture
async def chat_session(
    consumer: Consumer,
    supplier_sales_user: User,
    order: Order,
    db_session: AsyncSession,
) -> AsyncGenerator[ChatSession]:
    """Create a chat session for testing."""
    session = ChatSession(
        consumer_id=consumer.id,
        sales_rep_id=supplier_sales_user.id,
        order_id=order.id,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def complaint(
    consumer: Consumer,
    order: Order,
    supplier_sales_user: User,
    supplier_manager_user: User,
    db_session: AsyncSession,
) -> AsyncGenerator[Complaint]:
    """Create a complaint for testing."""
    complaint = Complaint(
        order_id=order.id,
        consumer_id=consumer.id,
        sales_rep_id=supplier_sales_user.id,
        manager_id=supplier_manager_user.id,
        status=ComplaintStatus.OPEN,
        description="Test complaint description",
    )
    db_session.add(complaint)
    await db_session.commit()
    await db_session.refresh(complaint)
    return complaint


@pytest.fixture
async def notification(
    consumer_user: User,
    db_session: AsyncSession,
) -> AsyncGenerator[Notification]:
    """Create a notification for testing."""
    notification = Notification(
        recipient_id=consumer_user.id,
        type="order_created",
        message="Your order has been created",
        is_read=False,
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)
    return notification


@pytest.fixture
async def auth_headers_consumer(
    client: AsyncClient,
    consumer_user: User,
) -> AsyncGenerator[dict[str, str]]:
    """Get authentication headers for consumer user."""
    # Login to get token
    login_data = {
        "email": consumer_user.email,
        "password": "Password123",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_supplier_owner(
    client: AsyncClient,
    supplier_owner_user: User,
) -> AsyncGenerator[dict[str, str]]:
    """Get authentication headers for supplier owner user."""
    login_data = {
        "email": supplier_owner_user.email,
        "password": "Password123",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_supplier_manager(
    client: AsyncClient,
    supplier_manager_user: User,
) -> AsyncGenerator[dict[str, str]]:
    """Get authentication headers for supplier manager user."""
    login_data = {
        "email": supplier_manager_user.email,
        "password": "Password123",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_supplier_sales(
    client: AsyncClient,
    supplier_sales_user: User,
) -> AsyncGenerator[dict[str, str]]:
    """Get authentication headers for supplier sales user."""
    login_data = {
        "email": supplier_sales_user.email,
        "password": "Password123",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
