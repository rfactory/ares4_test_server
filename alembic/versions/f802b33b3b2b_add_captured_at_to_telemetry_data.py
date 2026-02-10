"""Add captured_at to telemetry_data and ensure enum values

Revision ID: f802b33b3b2b
Revises: a5f8a17e1cd3
Create Date: 2026-02-10 02:58:16.252911

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f802b33b3b2b'
down_revision: Union[str, Sequence[str], None] = 'a5f8a17e1cd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. [보안] Enum 타입에 'TELEMETRY'가 없는 경우를 대비해 추가 (PostgreSQL 전용)
    # commit을 강제로 날려야 ALTER TYPE이 반영되므로 execute를 사용합니다.
    op.execute("COMMIT") 
    try:
        op.execute("ALTER TYPE observation_snapshot_type ADD VALUE 'TELEMETRY'")
    except Exception:
        # 이미 존재할 경우 에러가 나므로 무시합니다.
        pass

    # 2. device_component_instances 인덱스 교정
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
        unique=True
    )

    # 3. telemetry_data 테이블에 captured_at 컬럼 추가
    # nullable=False로 만들되, 기존 데이터가 있을 경우를 대비해 서버 시간을 기본값으로 임시 부여합니다.
    op.add_column(
        'telemetry_data', 
        sa.Column(
            'captured_at', 
            postgresql.TIMESTAMP(timezone=True), 
            nullable=False, 
            server_default=sa.func.now(),
            comment='센서에서 실제 측정된 시각'
        )
    )
    op.create_index(op.f('ix_telemetry_data_captured_at'), 'telemetry_data', ['captured_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_telemetry_data_captured_at'), table_name='telemetry_data')
    op.drop_column('telemetry_data', 'captured_at')
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context -> 'grid'::text) ->> 'row'::text), ((spatial_context -> 'grid'::text) ->> 'col'::text), ((spatial_context -> 'grid'::text) ->> 'layer'::text)")], 
        unique=True
    )