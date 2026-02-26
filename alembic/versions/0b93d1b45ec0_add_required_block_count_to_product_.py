"""Add required_block_count to product_lines

Revision ID: 0b93d1b45ec0
Revises: c93f10b0c59c
Create Date: 2026-02-26 05:48:17.052786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b93d1b45ec0'
down_revision: Union[str, Sequence[str], None] = 'c93f10b0c59c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # 1. [Index Cleanup] JSONB 인덱스 구문 정제 (Postgres 괄호 및 캐스팅 문제 해결)
    # Autogenerate가 만든 구문은 실제 적용 시 에러가 잦으므로 명시적 DROP/CREATE 처리
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [
            sa.text("((spatial_context->'grid'->>'row'))"), 
            sa.text("((spatial_context->'grid'->>'col'))"), 
            sa.text("((spatial_context->'grid'->>'layer'))")
        ], 
        unique=True
    )

    # 2. [Column Addition] required_block_count 추가
    # 기존 데이터가 존재할 경우 nullable=False 위반으로 실패하지 않도록 '1'을 server_default로 부여합니다.
    op.add_column('product_lines', 
        sa.Column('required_block_count', sa.Integer(), 
                  nullable=False, 
                  server_default='1', 
                  comment='가구 가동을 위한 필수 블록 개수 (정확히 이 개수여야 ACTIVE)')
    )


def downgrade() -> None:
    """Downgrade schema."""
    
    # 1. 컬럼 제거
    op.drop_column('product_lines', 'required_block_count')

    # 2. 인덱스 원복
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