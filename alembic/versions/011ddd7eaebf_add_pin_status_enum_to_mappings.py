"""add_pin_status_enum_to_mappings

Revision ID: 011ddd7eaebf
Revises: 4af55f619e42
Create Date: 2026-02-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011ddd7eaebf'
down_revision: Union[str, Sequence[str], None] = '4af55f619e42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. PostgreSQL 내부에 Enum 타입 생성 (이미 존재할 수 있으므로 checkfirst 적용)
    # 2단계 상태(ACTIVE, FAULTY)를 반영합니다.
    pin_status_enum = postgresql.ENUM('ACTIVE', 'FAULTY', name='pin_status_enum')
    pin_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. status 컬럼 추가 (기본값 ACTIVE)
    op.add_column('device_component_pin_mappings', 
        sa.Column('status', 
                  pin_status_enum, 
                  nullable=False, 
                  server_default='ACTIVE')
    )


def downgrade() -> None:
    # 1. status 컬럼 삭제
    op.drop_column('device_component_pin_mappings', 'status')

    # 2. Enum 타입 삭제 (선택 사항이지만 완전한 롤백을 위해 포함)
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        sa.postgresql.ENUM(name='pin_status_enum').drop(bind, checkfirst=True)