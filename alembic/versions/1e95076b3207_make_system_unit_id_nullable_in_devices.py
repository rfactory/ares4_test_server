"""make_system_unit_id_nullable_in_devices

Revision ID: 1e95076b3207
Revises: 5f4c50d11354
Create Date: 2026-02-10 06:06:42.182191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e95076b3207'
down_revision: Union[str, Sequence[str], None] = '5f4c50d11354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 불필요한 인덱스 변경(JSONB 등) 제거함 -> 에러 원인 차단
    # 2. 오직 devices 테이블의 system_unit_id 컬럼만 NULL 허용으로 변경
    op.alter_column('devices', 'system_unit_id',
               existing_type=sa.BIGINT(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # 롤백 시 다시 NOT NULL로 복구
    op.alter_column('devices', 'system_unit_id',
               existing_type=sa.BIGINT(),
               nullable=False)