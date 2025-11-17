"""Verify database schema matches Phase 3 requirements."""

import asyncio

from sqlalchemy import text

from app.db.session import engine


async def verify_database():
    """Verify all tables, columns, constraints, and indexes exist."""
    async with engine.connect() as conn:
        print("=" * 70)
        print("DATABASE SCHEMA VERIFICATION")
        print("=" * 70)

        # Check all tables exist
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE' "
                "ORDER BY table_name"
            )
        )
        tables = [row[0] for row in result]
        print(f"\n[1] Tables in database: {len(tables)}")
        for table in tables:
            print(f"    - {table}")

        expected_tables = [
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
        ]
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"    ERROR: Missing tables: {missing_tables}")
        else:
            print(f"    SUCCESS: All {len(expected_tables)} expected tables exist")

        # Check unique constraints
        print("\n[2] Unique Constraints:")
        result = await conn.execute(
            text(
                """
                SELECT constraint_name, table_name, column_name
                FROM information_schema.constraint_column_usage
                WHERE constraint_name IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'UNIQUE' AND table_schema = 'public'
                )
                ORDER BY table_name, constraint_name
                """
            )
        )
        unique_constraints = list(result)
        for constraint_name, table_name, column_name in unique_constraints:
            print(f"    - {table_name}.{constraint_name} ({column_name})")

        # Check foreign key constraints
        print("\n[3] Foreign Key Constraints:")
        result = await conn.execute(
            text(
                """
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON rc.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                ORDER BY tc.table_name, tc.constraint_name
                """
            )
        )
        foreign_keys = list(result)
        print(f"    Total foreign keys: {len(foreign_keys)}")
        for fk in foreign_keys[:10]:  # Show first 10
            (
                constraint_name,
                table_name,
                column_name,
                foreign_table,
                foreign_column,
                delete_rule,
            ) = fk
            print(
                f"    - {table_name}.{column_name} -> {foreign_table}.{foreign_column} (ON DELETE {delete_rule})"
            )
        if len(foreign_keys) > 10:
            print(f"    ... and {len(foreign_keys) - 10} more")

        # Check indexes
        print("\n[4] Indexes:")
        result = await conn.execute(
            text(
                """
                SELECT
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                    AND indexname NOT LIKE 'pg_%'
                ORDER BY tablename, indexname
                """
            )
        )
        indexes = list(result)
        print(f"    Total indexes: {len(indexes)}")
        table_indexes: dict[str, list[str]] = {}
        for table_name, index_name, _index_def in indexes:
            table_indexes.setdefault(table_name, []).append(index_name)

        for table in sorted(table_indexes.keys()):
            print(f"    {table}: {len(table_indexes[table])} indexes")

        # Check enum types
        print("\n[5] Enum Types:")
        result = await conn.execute(
            text(
                """
                SELECT typname, array_agg(enumlabel ORDER BY enumsortorder) as values
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE typname IN ('linkstatus', 'orderstatus', 'complaintstatus')
                GROUP BY typname
                ORDER BY typname
                """
            )
        )
        enums = list(result)
        for enum_name, enum_values in enums:
            values_str = ", ".join(enum_values)
            print(f"    - {enum_name}: {values_str}")

        # Verify key table structures
        print("\n[6] Key Table Structures:")
        key_tables = {
            "users": [
                "id",
                "email",
                "password_hash",
                "role",
                "is_active",
                "created_at",
            ],
            "products": ["id", "supplier_id", "name", "price_kzt", "sku", "stock_qty"],
            "orders": ["id", "supplier_id", "consumer_id", "status", "total_kzt"],
            "links": [
                "id",
                "consumer_id",
                "supplier_id",
                "status",
                "created_at",
                "updated_at",
            ],
        }

        for table_name, expected_columns in key_tables.items():
            if table_name not in tables:
                print(f"    ERROR: Table {table_name} not found")
                continue

            result = await conn.execute(
                text(
                    f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                    """
                )
            )
            actual_columns = {row[0] for row in result}
            missing_columns = [
                col for col in expected_columns if col not in actual_columns
            ]
            if missing_columns:
                print(f"    ERROR: {table_name} missing columns: {missing_columns}")
            else:
                print(f"    SUCCESS: {table_name} has all expected columns")

        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_database())
