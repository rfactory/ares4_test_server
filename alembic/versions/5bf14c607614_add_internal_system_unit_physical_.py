"""Add internal system unit physical component and refactor asset relationships

Revision ID: 5bf14c607614
Revises: ea0077d06513
Create Date: 2026-01-29 11:02:09.738683

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5bf14c607614'
down_revision: Union[str, Sequence[str], None] = 'ea0077d06513'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. PostgreSQL Enum 존재 여부 확인 및 생성 로직
    bind = op.get_bind()
    # pg_type에서 componentsourcetype이 이미 정의되어 있는지 확인합니다.
    has_type = bind.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'componentsourcetype')")
    ).scalar()

    if not has_type:
        # 타입이 없을 때만 명시적으로 생성합니다.
        op.execute("CREATE TYPE componentsourcetype AS ENUM ('INITIAL', 'WARRANTY', 'PAID_REPAIR', 'DIY_REPLACEMENT')")

    # 2. 신규 테이블 생성
    op.create_table('internal_system_unit_physical_components',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('position_tag', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        # create_type=False를 주어 테이블 생성 시점에 타입을 또 만들지 않도록 합니다.
        sa.Column('source_type', postgresql.ENUM('INITIAL', 'WARRANTY', 'PAID_REPAIR', 'DIY_REPLACEMENT', name='componentsourcetype', create_type=False), nullable=False),
        sa.Column('change_reason', sa.String(length=255), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('assembly_notes', sa.Text(), nullable=True),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('system_unit_id', sa.BigInteger(), nullable=False),
        sa.Column('asset_definition_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['asset_definition_id'], ['internal_asset_definitions.id'], ),
        sa.ForeignKeyConstraint(['system_unit_id'], ['system_units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_internal_system_unit_physical_components_id'), 'internal_system_unit_physical_components', ['id'], unique=False)
    op.create_index(op.f('ix_internal_system_unit_physical_components_position_tag'), 'internal_system_unit_physical_components', ['position_tag'], unique=False)
    op.create_index(op.f('ix_internal_system_unit_physical_components_system_unit_id'), 'internal_system_unit_physical_components', ['system_unit_id'], unique=False)

    # 3. 인덱스 수정 (JSONB 경로 인덱스)
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', [sa.text("(spatial_context->'grid'->>'row'), (spatial_context->'grid'->>'col'), (spatial_context->'grid'->>'layer')")], unique=True)
    
    # 4. ProductLine 리비전 추가 및 제약조건 갱신
    # 기존 데이터가 있을 경우 에러 방지를 위해 v1.0 기본값을 서버 측에 설정합니다.
    op.add_column('product_lines', sa.Column('revision', sa.String(length=50), server_default='v1.0', nullable=False))
    op.drop_constraint('product_lines_name_key', 'product_lines', type_='unique')
    op.create_unique_constraint('_name_revision_uc', 'product_lines', ['name', 'revision'])

def downgrade() -> None:
    # 역순 작업
    op.drop_constraint('_name_revision_uc', 'product_lines', type_='unique')
    op.create_unique_constraint('product_lines_name_key', 'product_lines', ['name'])
    op.drop_column('product_lines', 'revision')
    
    op.drop_table('internal_system_unit_physical_components')
    # 필요 시 Enum 타입을 삭제할 수 있으나, 일반적으로는 데이터를 위해 남겨두기도 합니다.
    # op.execute("DROP TYPE componentsourcetype")