"""make_org_id_nullable_in_assignments

Revision ID: 1135338f6169
Revises: d8258e464079
Create Date: 2026-01-27 06:58:02.571785

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1135338f6169'
down_revision: Union[str, Sequence[str], None] = 'd8258e464079'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # 1. user_organization_roles 테이블의 organization_id를 nullable=True로 변경
    op.alter_column('user_organization_roles', 'organization_id',
               existing_type=sa.BIGINT(),
               nullable=True)

def downgrade() -> None:
    """Downgrade schema."""
    # 1. 다시 nullable=False로 복구 (정리 완료)
    op.alter_column('user_organization_roles', 'organization_id',
               existing_type=sa.BIGINT(),
               nullable=False)