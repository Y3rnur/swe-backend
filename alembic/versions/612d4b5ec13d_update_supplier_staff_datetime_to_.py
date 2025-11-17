"""update_supplier_staff_datetime_to_timestamptz

Revision ID: 612d4b5ec13d
Revises: f4f7b05a1952
Create Date: 2025-11-17 20:15:25.196151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '612d4b5ec13d'
down_revision: Union[str, None] = 'f4f7b05a1952'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert SupplierStaff DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE supplier_staff ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE supplier_staff ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
