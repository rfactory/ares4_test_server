"""Add hardware specs and asset foreign key

Revision ID: 57991886e976
Revises: <자동 생성된 ID>
Create Date: 2026-02-09 00:14:38.440081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '57991886e976'
down_revision: Union[str, Sequence[str], None] = '<자동 생성된 ID>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ===============================================================
    # 1. HardwareBlueprint: 'specs' JSONB 컬럼 추가
    # ===============================================================
    op.add_column(
        'hardware_blueprints', 
        sa.Column('specs', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # ===============================================================
    # 2. InternalAssetDefinition: 'supported_component_id' FK 추가
    # ===============================================================
    op.add_column(
        'internal_asset_definitions', 
        sa.Column('supported_component_id', sa.BigInteger(), nullable=True)
    )
    
    # 외래키 제약조건 생성
    op.create_foreign_key(
        None, 
        'internal_asset_definitions', 
        'supported_components', 
        ['supported_component_id'], 
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # ===============================================================
    # 1. InternalAssetDefinition 롤백 (FK 삭제 -> 컬럼 삭제)
    # ===============================================================
    op.drop_constraint(None, 'internal_asset_definitions', type_='foreignkey')
    op.drop_column('internal_asset_definitions', 'supported_component_id')

    # ===============================================================
    # 2. HardwareBlueprint 롤백 (specs 컬럼 삭제)
    # ===============================================================
    op.drop_column('hardware_blueprints', 'specs')