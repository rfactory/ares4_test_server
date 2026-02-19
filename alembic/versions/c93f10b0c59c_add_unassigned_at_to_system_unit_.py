"""Add unassigned_at to system_unit_assignments

Revision ID: c93f10b0c59c
Revises: d50c7a4fb56b
Create Date: 2026-02-19 08:48:12.332109

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c93f10b0c59c'
down_revision: Union[str, Sequence[str], None] = 'd50c7a4fb56b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. device_component_instances 인덱스 보정 (JSONB 경로 추출 문법 최적화)
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context->'grid'->>'row'))"), 
         sa.text("((spatial_context->'grid'->>'col'))"), 
         sa.text("((spatial_context->'grid'->>'layer'))")], 
        unique=True
    )

    # 2. unassigned_at 컬럼 추가
    op.add_column(
        'system_unit_assignments', 
        sa.Column('unassigned_at', sa.DateTime(), nullable=True, comment='관계가 종료된 시점. Null이면 현재 소유/이용 중.')
    )
    op.create_index(op.f('ix_system_unit_assignments_unassigned_at'), 'system_unit_assignments', ['unassigned_at'], unique=False)

    # 3. 기존 OWNER 유일성 인덱스 제거 및 신규 인덱스(Soft Unbind 대응) 생성
    # PostgreSQL에서 Enum 비교 시 명시적 캐스팅(::assignment_role_type)이 필요할 수 있습니다.
    op.drop_index('ix_unique_unit_owner_constraint', table_name='system_unit_assignments')
    
    op.create_index(
        'ix_unique_active_unit_owner', 
        'system_unit_assignments', 
        ['system_unit_id'], 
        unique=True, 
        postgresql_where=sa.text("role = 'OWNER' AND unassigned_at IS NULL")
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 신규 인덱스 제거 및 이전 OWNER 인덱스 복구
    op.drop_index('ix_unique_active_unit_owner', table_name='system_unit_assignments', postgresql_where=sa.text("role = 'OWNER' AND unassigned_at IS NULL"))
    op.drop_index(op.f('ix_system_unit_assignments_unassigned_at'), table_name='system_unit_assignments')
    
    # 이전 인덱스 복구 (unassigned_at 조건 없음)
    op.create_index(
        'ix_unique_unit_owner_constraint', 
        'system_unit_assignments', 
        ['system_unit_id'], 
        unique=True, 
        postgresql_where=sa.text("role = 'OWNER'")
    )
    
    # 2. 컬럼 제거
    op.drop_column('system_unit_assignments', 'unassigned_at')

    # 3. device_component_instances 인덱스 원상 복구
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context -> 'grid'::text) ->> 'row'::text)"), 
         sa.text("((spatial_context -> 'grid'::text) ->> 'col'::text)"), 
         sa.text("((spatial_context -> 'grid'::text) ->> 'layer'::text)")], 
        unique=True
    )