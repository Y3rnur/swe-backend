"""update_chat_datetime_to_timestamptz

Revision ID: f4f7b05a1952
Revises: 4ac8bc3b4b99
Create Date: 2025-11-17 20:09:40.824940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f4f7b05a1952'
down_revision: Union[str, None] = '4ac8bc3b4b99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert ChatSession DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE chat_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )
    # Convert ChatMessage DateTime column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE chat_messages ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at::TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE chat_messages ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE chat_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at::TIMESTAMP WITHOUT TIME ZONE"
    )
