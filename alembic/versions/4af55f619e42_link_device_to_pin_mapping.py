"""link_device_to_pin_mapping

Revision ID: 4af55f619e42
Revises: 667ad21b6152
Create Date: 2026-02-12 02:23:25.834178

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4af55f619e42'
down_revision: Union[str, Sequence[str], None] = '667ad21b6152'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. device_id 컬럼은 이미 존재하므로 add_column은 생략합니다.
    # 대신 외래 키 제약 조건(Foreign Key)이 없다면 연결해줍니다.
    # (이미 연결되어 있다면 에러가 날 수 있으나, 보통 컬럼만 있고 제약 조건은 없는 경우가 많습니다.)
    try:
        op.create_foreign_key(
            'fk_device_component_pin_mappings_device_id_devices',
            'device_component_pin_mappings', 'devices',
            ['device_id'], ['id'],
            ondelete='CASCADE'
        )
    except Exception as e:
        print(f"⚠️ Foreign Key might already exist: {e}")

    # 2. (Alembic이 감지한) 인덱스 수정 - JSONB 데이터 추출 방식 정규화
    # 기존 인덱스를 드롭하고 정확한 literal_column 문법으로 다시 생성합니다.
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [
            sa.literal_column("((spatial_context->'grid'->>'row'))"), 
            sa.literal_column("((spatial_context->'grid'->>'col'))"), 
            sa.literal_column("((spatial_context->'grid'->>'layer'))")
        ], 
        unique=True
    )


def downgrade() -> None:
    # 1. 인덱스 원복
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [
            sa.literal_column("((spatial_context -> 'grid'::text) ->> 'row'::text)"), 
            sa.literal_column("((spatial_context -> 'grid'::text) ->> 'col'::text)"), 
            sa.literal_column("((spatial_context -> 'grid'::text) ->> 'layer'::text)")
        ], 
        unique=True
    )

    # 2. 외래 키 삭제
    op.drop_constraint('fk_device_component_pin_mappings_device_id_devices', 'device_component_pin_mappings', type_='foreignkey')
    
    # 3. 컬럼 삭제 (upgrade에서 생성하지 않았으므로 필요 시에만 수행하도록 주석 처리하거나 남겨둡니다.)
    # op.drop_column('device_component_pin_mappings', 'device_id')