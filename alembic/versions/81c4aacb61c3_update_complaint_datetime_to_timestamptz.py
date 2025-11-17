"""update_complaint_datetime_to_timestamptz

Revision ID: 81c4aacb61c3
Revises: 612d4b5ec13d
Create Date: 2025-11-17 20:22:13.488972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '81c4aacb61c3'
down_revision: Union[str, None] = '612d4b5ec13d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert Complaint DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE complaints ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE complaints ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
