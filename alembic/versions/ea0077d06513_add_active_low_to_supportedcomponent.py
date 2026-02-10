"""Add active_low to SupportedComponent

Revision ID: ea0077d06513
Revises: dabbc9fbb2d6
Create Date: 2026-01-29 08:15:48.745526

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ea0077d06513'
down_revision: Union[str, Sequence[str], None] = 'dabbc9fbb2d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    [핵심 공사] 
    supported_components 테이블에 active_low 컬럼을 추가합니다.
    기존 부품들은 기본값으로 False(Active-HIGH)가 설정됩니다.
    """
    op.add_column(
        'supported_components', 
        sa.Column('active_low', sa.Boolean(), server_default='false', nullable=False)
    )


def downgrade() -> None:
    """
    [롤백 로직]
    추가했던 active_low 컬럼을 제거하여 이전 상태(dabbc9fbb2d6)로 되돌립니다.
    """
    op.drop_column('supported_components', 'active_low')