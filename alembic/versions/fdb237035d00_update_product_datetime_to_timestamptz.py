"""update_product_datetime_to_timestamptz

Revision ID: fdb237035d00
Revises: ff5d60414338
Create Date: 2025-11-17 19:24:35.422569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdb237035d00'
down_revision: Union[str, None] = 'ff5d60414338'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert Product DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE products ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE products ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
