"""change_datetime_to_timestamptz

Revision ID: e241c7628de0
Revises: f69fa72f36e7
Create Date: 2025-11-17 19:04:14.932277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e241c7628de0'
down_revision: Union[str, None] = 'f69fa72f36e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert all DateTime columns to TIMESTAMP WITH TIME ZONE
    tables_and_columns = [
        ('users', 'created_at'),
        ('suppliers', 'created_at'),
        ('consumers', 'created_at'),
        ('supplier_staff', 'created_at'),
        ('notifications', 'created_at'),
        ('links', 'created_at'),
        ('links', 'updated_at'),
        ('orders', 'created_at'),
        ('chat_sessions', 'created_at'),
        ('chat_messages', 'created_at'),
        ('complaints', 'created_at'),
    ]

    for table, column in tables_and_columns:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITH TIME ZONE USING {column}::TIMESTAMP WITH TIME ZONE"
        )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    tables_and_columns = [
        ('users', 'created_at'),
        ('suppliers', 'created_at'),
        ('consumers', 'created_at'),
        ('supplier_staff', 'created_at'),
        ('notifications', 'created_at'),
        ('links', 'created_at'),
        ('links', 'updated_at'),
        ('orders', 'created_at'),
        ('chat_sessions', 'created_at'),
        ('chat_messages', 'created_at'),
        ('complaints', 'created_at'),
    ]

    for table, column in tables_and_columns:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITHOUT TIME ZONE USING {column}::TIMESTAMP WITHOUT TIME ZONE"
        )
