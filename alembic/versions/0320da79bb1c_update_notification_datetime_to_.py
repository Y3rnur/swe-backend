"""update_notification_datetime_to_timestamptz

Revision ID: 0320da79bb1c
Revises: 81c4aacb61c3
Create Date: 2025-11-17 20:32:54.836688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0320da79bb1c'
down_revision: Union[str, None] = '81c4aacb61c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert Notification DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE notifications ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
