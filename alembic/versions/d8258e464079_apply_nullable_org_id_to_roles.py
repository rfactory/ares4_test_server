"""apply_nullable_org_id_to_roles

Revision ID: d8258e464079
Revises: ac9de54ed9d0
Create Date: 2026-01-27 06:46:54.651422

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd8258e464079'
down_revision: Union[str, Sequence[str], None] = 'ac9de54ed9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # 1. roles 테이블의 organization_id를 nullable=True로 변경
    op.alter_column('roles', 'organization_id',
               existing_type=sa.BIGINT(),
               nullable=True)

def downgrade() -> None:
    """Downgrade schema."""
    # 1. 다시 nullable=False로 복구
    op.alter_column('roles', 'organization_id',
               existing_type=sa.BIGINT(),
               nullable=False)