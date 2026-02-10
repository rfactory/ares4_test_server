"""make_blueprint_nullable

Revision ID: 4f0c135f2327
Revises: 1e95076b3207
Create Date: 2026-02-10 06:22:05.646344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f0c135f2327'
down_revision: Union[str, Sequence[str], None] = '1e95076b3207'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 불필요한 인덱스 변경 제거함 (에러 방지)
    # hardware_blueprint_id 컬럼을 NULL 허용으로 변경
    op.alter_column('devices', 'hardware_blueprint_id',
               existing_type=sa.BIGINT(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # 롤백 시 다시 NOT NULL로 복구
    op.alter_column('devices', 'hardware_blueprint_id',
               existing_type=sa.BIGINT(),
               nullable=False)