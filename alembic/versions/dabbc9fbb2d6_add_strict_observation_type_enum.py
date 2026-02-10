"""add_strict_observation_type_enum

Revision ID: dabbc9fbb2d6
Revises: 8fc8b40e97bc
Create Date: 2026-01-27 18:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dabbc9fbb2d6'
down_revision: Union[str, Sequence[str], None] = '8fc8b40e97bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. 새로운 Enum 타입을 DB에 명시적으로 생성합니다.
    observation_type_enum = postgresql.ENUM('IMAGE', 'SENSOR', 'LOG', 'ALARM', 'COMMAND', name='observation_type')
    observation_type_enum.create(op.get_bind(), checkfirst=True)

    # 2. observation_snapshots 테이블에 컬럼을 추가합니다.
    # 다니엘님의 보안 철학에 따라 nullable=False로 설정합니다.
    op.add_column('observation_snapshots', 
        sa.Column('observation_type', sa.Enum('IMAGE', 'SENSOR', 'LOG', 'ALARM', 'COMMAND', name='observation_type'), nullable=False)
    )

def downgrade() -> None:
    # 원복 시 컬럼을 삭제하고 Enum 타입을 제거합니다.
    op.drop_column('observation_snapshots', 'observation_type')
    op.execute('DROP TYPE observation_type')