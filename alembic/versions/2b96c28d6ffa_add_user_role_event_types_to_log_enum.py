"""Add user role event types to log enum

Revision ID: 2b96c28d6ffa
Revises: b200ff1db912
Create Date: 2026-01-05 07:25:09.093269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b96c28d6ffa'
down_revision: Union[str, Sequence[str], None] = 'b200ff1db912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE log_event_type ADD VALUE IF NOT EXISTS 'USER_ROLE_ASSIGNED'")
    op.execute("ALTER TYPE log_event_type ADD VALUE IF NOT EXISTS 'USER_ROLE_REVOKED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Enum downgrade is complex, skipping.
    pass
