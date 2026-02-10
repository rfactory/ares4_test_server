"""fix_system_unit_role_assignments_relationship
Revision ID: ad016aeec15d
Revises: 2226c613e141
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ad016aeec15d'
down_revision: Union[str, Sequence[str], None] = '2226c613e141'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 인덱스 재생성 (기존 인덱스 존재 시 에러 방지)
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', 
                   [sa.literal_column("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
                   unique=True)

    # 2. 컬럼 주석 및 메타데이터 정렬 (Any 타입 방지 및 가독성 향상)
    op.alter_column('device_component_instances', 'spatial_context',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               comment='grid(좌표), physical(실측), operating_limits(SLA) 포함',
               existing_nullable=False)

    op.alter_column('observation_snapshots', 'observation_type',
               existing_type=postgresql.ENUM('IMAGE', 'SENSOR', 'LOG', 'ALARM', 'COMMAND', name='observation_snapshot_type'),
               comment='데이터 정체성 (IMAGE, SENSOR 등)',
               existing_nullable=False)

    op.alter_column('telemetry_data', 'metric_name',
               existing_type=sa.VARCHAR(length=100),
               comment='측정 항목명 (temp, co2 등)',
               existing_nullable=False)

    op.alter_column('vision_features', 'model_version',
               existing_type=sa.VARCHAR(length=50),
               comment='추출에 사용된 AI 모델 명칭 및 버전 (예: SAM3-v1)',
               existing_nullable=False)

    # 3. 매퍼 초기화용 관계 설정 (Relationship fix)
    # 이 부분은 코드로 반영되었으므로 DB 레벨에서는 변경사항이 없어도 버전 관리를 위해 Head를 유지합니다.

def downgrade() -> None:
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')