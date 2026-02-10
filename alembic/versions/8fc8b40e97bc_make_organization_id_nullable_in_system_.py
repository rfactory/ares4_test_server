"""make_organization_id_nullable_in_system_units

Revision ID: 8fc8b40e97bc
Revises: 1135338f6169
Create Date: 2026-01-27 09:14:48.461588

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8fc8b40e97bc'
down_revision: Union[str, Sequence[str], None] = '1135338f6169'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # 1. SystemUnit의 organization_id 제약 조건을 Nullable로 변경 (핵심 작업)
    op.alter_column('system_units', 'organization_id',
               existing_type=sa.BIGINT(),
               nullable=True)

def downgrade() -> None:
    """Downgrade schema."""
    # 원복 시 다시 NOT NULL로 변경
    op.alter_column('system_units', 'organization_id',
               existing_type=sa.BIGINT(),
               nullable=False)