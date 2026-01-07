"""Add access request event types to log enum

Revision ID: b200ff1db912
Revises: b7484d83c8e5
Create Date: 2026-01-05 01:40:23.820192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b200ff1db912'
down_revision: Union[str, Sequence[str], None] = 'b7484d83c8e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE log_event_type ADD VALUE IF NOT EXISTS 'ACCESS_REQUEST_CREATED'")
    op.execute("ALTER TYPE log_event_type ADD VALUE IF NOT EXISTS 'ACCESS_REQUEST_UPDATED'")
    op.execute("ALTER TYPE log_event_type ADD VALUE IF NOT EXISTS 'ACCESS_REQUEST_DELETED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrading an enum is complex and can lead to data loss.
    # It's often safer to leave the enum as is.
    pass
