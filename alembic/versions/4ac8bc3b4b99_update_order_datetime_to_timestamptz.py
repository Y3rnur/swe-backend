"""update_order_datetime_to_timestamptz

Revision ID: 4ac8bc3b4b99
Revises: fdb237035d00
Create Date: 2025-11-17 19:34:44.692959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ac8bc3b4b99'
down_revision: Union[str, None] = 'fdb237035d00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert Order DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE orders ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE orders ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
