"""decouple_provisioning_token_from_user_and_org

Revision ID: d50c7a4fb56b
Revises: ac5a90ac9a10
Create Date: 2026-02-13 06:36:35.340356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # 필요시 사용

# revision identifiers, used by Alembic.
revision: str = 'd50c7a4fb56b'
down_revision: Union[str, Sequence[str], None] = 'ac5a90ac9a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # 1. InternalAssetInventory에 조직 연결 추가 (누락되었던 FK)
    # (이미 존재한다면 이 부분은 주석 처리하거나 에러 날 수 있음. 확인 필요)
    # op.add_column('internal_asset_inventory', sa.Column('organization_id', sa.BigInteger(), nullable=True))
    # op.create_index(op.f('ix_internal_asset_inventory_organization_id'), 'internal_asset_inventory', ['organization_id'], unique=False)
    # op.create_foreign_key(None, 'internal_asset_inventory', 'organizations', ['organization_id'], ['id'])
    
    # [다니엘님 확인: InternalAssetInventory 모델을 이번에 수정하지 않았다면 위 3줄은 지우세요. 
    #  하지만 아까 모델 관계 설정할 때 건드렸다면 포함해야 합니다. 안전하게 포함해둡니다.]
    op.add_column('internal_asset_inventory', sa.Column('organization_id', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_internal_asset_inventory_organization_id'), 'internal_asset_inventory', ['organization_id'], unique=False)
    op.create_foreign_key('fk_internal_asset_inventory_organization_id', 'internal_asset_inventory', 'organizations', ['organization_id'], ['id'])

    # 2. ProvisioningToken 구조 변경 (핵심: 소유권 분리)
    op.add_column('provisioning_tokens', sa.Column('used_at', sa.DateTime(timezone=True), nullable=True))
    
    # 기존 FK 제약조건 삭제 (이름이 다를 수 있으니 DB 확인 권장하지만, 보통 autogenerate가 맞음)
    op.drop_constraint('provisioning_tokens_issued_by_user_id_fkey', 'provisioning_tokens', type_='foreignkey')
    op.drop_constraint('provisioning_tokens_issued_by_organization_id_fkey', 'provisioning_tokens', type_='foreignkey')
    
    # 컬럼 삭제
    op.drop_column('provisioning_tokens', 'issued_by_organization_id')
    op.drop_column('provisioning_tokens', 'issued_by_user_id')


def downgrade() -> None:
    """Downgrade schema."""
    
    # 1. ProvisioningToken 복구
    op.add_column('provisioning_tokens', sa.Column('issued_by_user_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('provisioning_tokens', sa.Column('issued_by_organization_id', sa.BIGINT(), autoincrement=False, nullable=True))
    
    op.create_foreign_key('provisioning_tokens_issued_by_organization_id_fkey', 'provisioning_tokens', 'organizations', ['issued_by_organization_id'], ['id'])
    op.create_foreign_key('provisioning_tokens_issued_by_user_id_fkey', 'provisioning_tokens', 'users', ['issued_by_user_id'], ['id'])
    
    op.drop_column('provisioning_tokens', 'used_at')

    # 2. InternalAssetInventory 복구
    op.drop_constraint('fk_internal_asset_inventory_organization_id', 'internal_asset_inventory', type_='foreignkey')
    op.drop_index(op.f('ix_internal_asset_inventory_organization_id'), table_name='internal_asset_inventory')
    op.drop_column('internal_asset_inventory', 'organization_id')