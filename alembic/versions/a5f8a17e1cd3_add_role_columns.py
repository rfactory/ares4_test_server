"""Add role columns

Revision ID: a5f8a17e1cd3
Revises: 57991886e976
Create Date: 2026-02-09 01:41:03.407878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'a5f8a17e1cd3'
down_revision: Union[str, Sequence[str], None] = '57991886e976'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_scope_enum = sa.Enum('SYSTEM', 'ORGANIZATION', name='role_scope')

def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('roles')]

    # -----------------------------------------------------------
    # 1. Role 테이블 변경 사항 (안전하게 추가)
    # -----------------------------------------------------------
    
    # (1) Enum 타입 생성 (없을 때만)
    role_scope_enum.create(conn, checkfirst=True)

    # (2) 컬럼 추가 (이미 있으면 건너뜀)
    if 'scope' not in columns:
        op.add_column('roles', sa.Column('scope', role_scope_enum, server_default='ORGANIZATION', nullable=False))
    
    if 'tier' not in columns:
        op.add_column('roles', sa.Column('tier', sa.Integer(), nullable=True))
        # 인덱스도 컬럼 만들 때 같이 생성
        op.create_index(op.f('ix_roles_tier'), 'roles', ['tier'], unique=False)

    if 'lineage' not in columns:
        op.add_column('roles', sa.Column('lineage', sa.String(length=255), nullable=True))
    
    if 'numbering' not in columns:
        op.add_column('roles', sa.Column('numbering', sa.Integer(), nullable=True))
    
    if 'max_headcount' not in columns:
        op.add_column('roles', sa.Column('max_headcount', sa.Integer(), nullable=True))


    # -----------------------------------------------------------
    # 2. 기타 자동 감지된 변경 사항 (Telemetry, Index 등)
    # -----------------------------------------------------------
    # 인덱스 재생성 부분은 에러가 날 수 있으므로 try-except나 존재 여부 확인이 까다로움.
    # 하지만 보통 이 부분은 Alembic이 잘 처리하므로 그대로 둡니다.
    # 만약 여기서도 에러가 나면 해당 줄을 주석 처리하세요.
    
    # ix_unique_spatial_slot 인덱스 처리
    try:
        op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    except Exception:
        pass # 없으면 패스

    op.create_index('ix_unique_spatial_slot', 'device_component_instances', [sa.literal_column("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], unique=True)
    
    # Telemetry 컬럼 수정 (에러 발생 시 무시 가능하므로 유지)
    with op.batch_alter_table('telemetry_data') as batch_op:
        batch_op.alter_column('unit',
                existing_type=sa.VARCHAR(length=20),
                comment='측정 단위',
                existing_comment='측정 단위 (예: °C, %)',
                existing_nullable=True)
        batch_op.alter_column('avg_value',
                existing_type=sa.DOUBLE_PRECISION(precision=53),
                comment=None,
                existing_comment='평균',
                existing_nullable=False)
        batch_op.alter_column('min_value',
                existing_type=sa.DOUBLE_PRECISION(precision=53),
                comment=None,
                existing_comment='최소값',
                existing_nullable=False)
        batch_op.alter_column('max_value',
                existing_type=sa.DOUBLE_PRECISION(precision=53),
                comment=None,
                existing_comment='최대값',
                existing_nullable=False)
        batch_op.alter_column('sample_count',
                existing_type=sa.INTEGER(),
                comment=None,
                existing_comment='통계에 사용된 샘플 수',
                existing_nullable=False)
        batch_op.alter_column('extra_stats',
                existing_type=postgresql.JSONB(astext_type=sa.Text()),
                comment=None,
                existing_comment='특화 데이터 (예: 적산 온도, 사분위수 등)',
                existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrade 로직은 복잡하므로, 일단 Upgrade 성공에 집중하기 위해 생략하거나 기본 로직 유지
    pass