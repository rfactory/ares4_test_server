"""Add organization event types to log enum

Revision ID: 1337bad63175
Revises: d81488a4be1a
Create Date: 2025-12-19 05:14:38.555077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1337bad63175'
down_revision: Union[str, Sequence[str], None] = 'd81488a4be1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE log_event_type ADD VALUE 'ORGANIZATION_CREATED'")
    op.execute("ALTER TYPE log_event_type ADD VALUE 'ORGANIZATION_UPDATED'")
    op.execute("ALTER TYPE log_event_type ADD VALUE 'ORGANIZATION_DELETED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrading enum values can be complex and data-dependent, so we will not implement it for now.
    # In a real production scenario, this would need careful handling.
    pass
