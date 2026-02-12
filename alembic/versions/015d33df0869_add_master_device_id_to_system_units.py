"""Add master_device_id to system_units

Revision ID: 015d33df0869
Revises: 931ea5e3b8e5
Create Date: 2026-02-11 23:43:24.877467

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '015d33df0869'
down_revision: Union[str, Sequence[str], None] = '931ea5e3b8e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. [노이즈 제거] JSONB 인덱스 관련 중복 코드는 삭제하고 핵심 컬럼만 추가합니다.
    
    # 2. system_units 테이블에 master_device_id 컬럼 추가
    op.add_column('system_units', 
        sa.Column('master_device_id', sa.BigInteger(), 
                  nullable=True, 
                  comment='클러스터의 텔레메트리 전송을 담당하는 마스터 기기')
    )

    # 3. 외래키(ForeignKey) 제약 조건 생성
    # 제약 조건 이름(_master_device_fk)을 명시하여 나중에 관리하기 편하게 합니다.
    op.create_foreign_key(
        '_system_units_master_device_fk', 
        'system_units', 'devices', 
        ['master_device_id'], ['id'], 
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 외래키 먼저 삭제 후 컬럼 삭제
    op.drop_constraint('_system_units_master_device_fk', 'system_units', type_='foreignkey')
    op.drop_column('system_units', 'master_device_id')