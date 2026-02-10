"""fix_system_unit_final_relationships
Revision ID: 830ff77561df
Revises: ad016aeec15d
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '830ff77561df'
down_revision: Union[str, Sequence[str], None] = 'ad016aeec15d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 인덱스 안전한 재생성 (Expression Index)
    # 이미 존재하는 인덱스를 먼저 지우고 새로 생성하여 에러 방지
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', 
                   [sa.literal_column("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
                   unique=True)

    # 2. 컬럼 주석(Comment) 일괄 업데이트 (Any 타입 방지 및 가독성 확보)
    op.alter_column('internal_asset_purchase_records', 'supplier_name', comment='공급업체 명')
    op.alter_column('internal_asset_purchase_records', 'invoice_number', comment='송장 번호')
    
    op.alter_column('organization_subscriptions', 'system_unit_id', 
                    comment='이 구독권이 할당된 유닛. Null일 경우 아직 미할당된 티켓.')

    op.alter_column('telemetry_data', 'unit', comment='측정 단위 (예: °C, %)')
    op.alter_column('telemetry_data', 'slope', comment='추세(기울기) 지표')
    op.alter_column('telemetry_data', 'sample_count', comment='통계에 사용된 샘플 수')
    
    # extra_stats는 JSONB 타입이므로 기존 타입을 명시해줘야 안전함
    op.alter_column('telemetry_data', 'extra_stats',
                    comment='특화 데이터 (예: 적산 온도, 사분위수 등)',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()))

    op.alter_column('vision_features', 'snapshot_id', comment='RL State 구성을 위한 시점 동기화 키')


def downgrade() -> None:
    # 롤백 시 인덱스 삭제
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    # 코멘트는 굳이 원복하지 않아도 됨