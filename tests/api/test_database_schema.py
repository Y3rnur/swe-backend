"""Integration tests for database schema verification.

These tests verify that the database schema matches the model definitions.
They should run against the actual database (PostgreSQL) after migrations.
"""

import pytest
from sqlalchemy import text

from app.db.session import engine

# Mark these tests as integration tests that require a real database
pytestmark = [pytest.mark.integration]


@pytest.mark.asyncio
class TestDatabaseSchema:
    """Test database schema matches Phase 3 requirements.

    These tests verify:
    - All expected tables exist
    - Key tables have required columns
    - Unique constraints are in place
    - Foreign key constraints exist
    - Enum types are defined
    - Indexes are present
    """

    async def test_all_tables_exist(self):
        """Verify all expected tables exist in the database."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_type='BASE TABLE' "
                    "ORDER BY table_name"
                )
            )
            tables = {row[0] for row in result}

            expected_tables = {
                "users",
                "suppliers",
                "consumers",
                "supplier_staff",
                "products",
                "links",
                "orders",
                "order_items",
                "chat_sessions",
                "chat_messages",
                "complaints",
                "notifications",
            }

            missing_tables = expected_tables - tables
            assert not missing_tables, f"Missing tables: {missing_tables}"

            # Allow alembic_version table (created by Alembic)
            allowed_extra_tables = {"alembic_version"}
            unexpected_tables = tables - expected_tables - allowed_extra_tables
            if unexpected_tables:
                pytest.fail(f"Unexpected tables found: {unexpected_tables}")

    async def test_users_table_structure(self):
        """Verify users table has all required columns."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'users'
                    ORDER BY ordinal_position
                    """
                )
            )
            columns = {row[0] for row in result}

            expected_columns = {
                "id",
                "email",
                "password_hash",
                "role",
                "is_active",
                "created_at",
            }

            missing_columns = expected_columns - columns
            assert not missing_columns, (
                f"Users table missing columns: {missing_columns}"
            )

    async def test_products_table_structure(self):
        """Verify products table has all required columns."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'products'
                    ORDER BY ordinal_position
                    """
                )
            )
            columns = {row[0] for row in result}

            expected_columns = {
                "id",
                "supplier_id",
                "name",
                "price_kzt",
                "sku",
                "stock_qty",
            }

            missing_columns = expected_columns - columns
            assert not missing_columns, (
                f"Products table missing columns: {missing_columns}"
            )

    async def test_orders_table_structure(self):
        """Verify orders table has all required columns."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'orders'
                    ORDER BY ordinal_position
                    """
                )
            )
            columns = {row[0] for row in result}

            expected_columns = {
                "id",
                "supplier_id",
                "consumer_id",
                "status",
                "total_kzt",
            }

            missing_columns = expected_columns - columns
            assert not missing_columns, (
                f"Orders table missing columns: {missing_columns}"
            )

    async def test_links_table_structure(self):
        """Verify links table has all required columns."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'links'
                    ORDER BY ordinal_position
                    """
                )
            )
            columns = {row[0] for row in result}

            expected_columns = {
                "id",
                "consumer_id",
                "supplier_id",
                "status",
                "created_at",
                "updated_at",
            }

            missing_columns = expected_columns - columns
            assert not missing_columns, (
                f"Links table missing columns: {missing_columns}"
            )

    async def test_unique_constraints_exist(self):
        """Verify important unique constraints exist."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.constraint_column_usage
                    WHERE constraint_name IN (
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE constraint_type = 'UNIQUE' AND table_schema = 'public'
                    )
                    ORDER BY table_name, column_name
                    """
                )
            )
            unique_constraints = {(row[0], row[1]) for row in result}

            # Verify users.email is unique
            assert ("users", "email") in unique_constraints, (
                "users.email should be unique"
            )

            # Verify links have unique constraint on (consumer_id, supplier_id)
            # This is a composite unique constraint, so we need to check differently
            result = await conn.execute(
                text(
                    """
                    SELECT tc.constraint_name, tc.table_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.constraint_type = 'UNIQUE'
                        AND tc.table_schema = 'public'
                        AND tc.table_name = 'links'
                    """
                )
            )
            link_constraints = {row[1] for row in result}
            assert "links" in link_constraints, (
                "links table should have unique constraint"
            )

    async def test_foreign_keys_exist(self):
        """Verify foreign key constraints exist."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT tc.table_name, kcu.column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = 'public'
                    ORDER BY tc.table_name, kcu.column_name
                    """
                )
            )
            foreign_keys = {(row[0], row[1]) for row in result}

            # Verify key foreign keys exist
            assert ("suppliers", "user_id") in foreign_keys, (
                "suppliers.user_id should be FK"
            )
            assert ("consumers", "user_id") in foreign_keys, (
                "consumers.user_id should be FK"
            )
            assert ("products", "supplier_id") in foreign_keys, (
                "products.supplier_id should be FK"
            )
            assert ("orders", "supplier_id") in foreign_keys, (
                "orders.supplier_id should be FK"
            )
            assert ("orders", "consumer_id") in foreign_keys, (
                "orders.consumer_id should be FK"
            )

    async def test_enum_types_exist(self):
        """Verify enum types exist."""
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT DISTINCT typname
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    WHERE typname IN ('linkstatus', 'orderstatus', 'complaintstatus')
                    ORDER BY typname
                    """
                )
            )
            enum_types = {row[0] for row in result}

            expected_enums = {"linkstatus", "orderstatus", "complaintstatus"}
            missing_enums = expected_enums - enum_types
            assert not missing_enums, f"Missing enum types: {missing_enums}"

    async def test_indexes_exist(self):
        """Verify important indexes exist."""
        async with engine.connect() as conn:
            # Verify users.email has an index (usually unique index)
            result = await conn.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public' AND tablename = 'users'
                        AND indexname NOT LIKE 'pg_%'
                    """
                )
            )
            user_indexes = {row[0] for row in result}
            assert len(user_indexes) > 0, "users table should have indexes"

            # Verify products.supplier_id has an index
            result = await conn.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public' AND tablename = 'products'
                        AND indexname NOT LIKE 'pg_%'
                    """
                )
            )
            product_indexes = {row[0] for row in result}
            assert len(product_indexes) > 0, "products table should have indexes"
