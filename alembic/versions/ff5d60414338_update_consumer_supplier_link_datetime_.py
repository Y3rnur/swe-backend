"""update_consumer_supplier_link_datetime_to_timestamptz

Revision ID: ff5d60414338
Revises: e241c7628de0
Create Date: 2025-11-17 19:17:34.797310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff5d60414338'
down_revision: Union[str, None] = 'e241c7628de0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert Consumer and Supplier DateTime columns to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE consumers ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE suppliers ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )
    # Links table was already updated in previous migration, but ensure updated_at is also converted
    op.execute(
        "ALTER TABLE links ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE links ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE consumers ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE suppliers ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE links ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE links ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at::TIMESTAMP WITHOUT TIME ZONE"
    )
