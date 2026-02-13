"""refactor_system_unit_assignments5

Revision ID: eb6ee5ec42d4
Revises: 8379fb20e9d8
Create Date: 2026-02-13 04:52:02.346786

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'eb6ee5ec42d4'
down_revision: Union[str, Sequence[str], None] = '8379fb20e9d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # 1. 인덱스 처리 (JSONB 공간 슬롯 인덱스 최적화)
    op.drop_index(op.f('ix_unique_spatial_slot'), table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
        unique=True
    )

    # 2. internal_asset_inventory 컬럼 체크 및 처리
    # 모델에 정의된 'recorded_by_organization_id'가 DB에 있는지 확인합니다.
    columns = [c['name'] for c in inspector.get_columns('internal_asset_inventory')]
    
    # 만약 Mixin이 생성하려고 한 'organization_id'가 들어왔다면 무시하거나 
    # 실제 사용하는 'recorded_by_organization_id'로 통합해야 합니다.
    target_col = 'recorded_by_organization_id'
    
    if target_col not in columns:
        op.add_column('internal_asset_inventory', sa.Column(target_col, sa.BigInteger(), nullable=True))
        op.create_index(op.f(f'ix_internal_asset_inventory_{target_col}'), 'internal_asset_inventory', [target_col], unique=False)
        op.create_foreign_key(f'fk_asset_inventory_org_{target_col}', 'internal_asset_inventory', 'organizations', [target_col], ['id'])

    # 3. internal_asset_purchase_records 컬럼 체크
    purchase_columns = [c['name'] for c in inspector.get_columns('internal_asset_purchase_records')]
    purchase_target = 'recorded_by_organization_id'
    
    if purchase_target not in purchase_columns:
        op.add_column('internal_asset_purchase_records', sa.Column(purchase_target, sa.BigInteger(), nullable=True))
        op.create_index(op.f(f'ix_asset_purchase_{purchase_target}'), 'internal_asset_purchase_records', [purchase_target], unique=False)
        op.create_foreign_key(f'fk_asset_purchase_org_{purchase_target}', 'internal_asset_purchase_records', 'organizations', [purchase_target], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 인덱스 원복
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        op.f('ix_unique_spatial_slot'), 
        'device_component_instances', 
        [sa.text("((spatial_context -> 'grid'::text) ->> 'row'::text)"), sa.text("((spatial_context -> 'grid'::text) ->> 'col'::text)"), sa.text("((spatial_context -> 'grid'::text) ->> 'layer'::text)")], 
        unique=True
    )
    # 컬럼 삭제 로직은 운영 안정성을 위해 pass 처리 권장
    pass