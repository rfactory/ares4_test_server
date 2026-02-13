"""refactor_system_unit_assignments6

Revision ID: ac5a90ac9a10
Revises: eb6ee5ec42d4
Create Date: 2026-02-13 05:02:49.490798

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'ac5a90ac9a10'
down_revision: Union[str, Sequence[str], None] = 'eb6ee5ec42d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # 1. DeviceComponentInstances 인덱스 최적화
    op.drop_index(op.f('ix_unique_spatial_slot'), table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
        unique=True
    )

    # 2. InternalAssetInventory 컬럼 정리 (organization_id 중복 생성 방지 및 명칭 통일)
    columns_inv = [c['name'] for c in inspector.get_columns('internal_asset_inventory')]
    if 'recorded_by_organization_id' not in columns_inv:
        op.add_column('internal_asset_inventory', sa.Column('recorded_by_organization_id', sa.BigInteger(), nullable=True))
        op.create_index(op.f('ix_internal_asset_inventory_recorded_by_organization_id'), 'internal_asset_inventory', ['recorded_by_organization_id'], unique=False)
        op.create_foreign_key('fk_asset_inventory_org_rec', 'internal_asset_inventory', 'organizations', ['recorded_by_organization_id'], ['id'])

    # 3. ProvisioningTokens 설계 변경 (Device 중심 -> 유닛 중심 1:1)
    columns_tokens = [c['name'] for c in inspector.get_columns('provisioning_tokens')]
    
    # device_id 삭제 (존재할 경우)
    if 'device_id' in columns_tokens:
        # 외래키 제약조건 이름은 DB마다 다를 수 있으나 자동 생성된 이름을 참조하여 삭제
        try:
            op.drop_constraint('provisioning_tokens_device_id_fkey', 'provisioning_tokens', type_='foreignkey')
            op.drop_constraint('provisioning_tokens_device_id_key', 'provisioning_tokens', type_='unique')
        except:
            pass
        op.drop_column('provisioning_tokens', 'device_id')

    # system_unit_id를 UNIQUE로 변경 (1:1 보장)
    op.drop_index(op.f('ix_provisioning_tokens_system_unit_id'), table_name='provisioning_tokens')
    op.create_unique_constraint('uq_provisioning_tokens_unit_id', 'provisioning_tokens', ['system_unit_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 운영 중 데이터 손실 방지를 위해 downgrade는 기본적인 인덱스 원복만 수행
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        op.f('ix_unique_spatial_slot'), 
        'device_component_instances', 
        [sa.text("((spatial_context -> 'grid'::text) ->> 'row'::text)"), sa.text("((spatial_context -> 'grid'::text) ->> 'col'::text)"), sa.text("((spatial_context -> 'grid'::text) ->> 'layer'::text)")], 
        unique=True
    )
    pass