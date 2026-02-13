"""refactor_system_unit_assignments3

Revision ID: 2c8fc092c48d
Revises: 40f2540298c7
Create Date: 2026-02-13 04:34:41.184077

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# --- Alembic 필수 변수 (이 부분이 누락되면 에러가 발생합니다) ---
revision: str = '2c8fc092c48d'
down_revision: Union[str, Sequence[str], None] = '40f2540298c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 인덱스 처리
    op.drop_index(op.f('ix_unique_spatial_slot'), table_name='device_component_instances')
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

    # 2. 새 Enum 타입 생성 (에러 방지용)
    op.execute("DO $$ BEGIN CREATE TYPE currencytype AS ENUM ('KRW', 'USD'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # 3. 컬럼 타입 변경
    op.alter_column('organizations', 'currency',
               existing_type=postgresql.ENUM('KRW', 'USD', name='currency_type'),
               type_=sa.Enum('KRW', 'USD', name='currencytype'),
               existing_nullable=True,
               postgresql_using="currency::text::currencytype")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 컬럼 타입 원복
    op.alter_column('organizations', 'currency',
               existing_type=sa.Enum('KRW', 'USD', name='currencytype'),
               type_=postgresql.ENUM('KRW', 'USD', name='currency_type'),
               existing_nullable=True,
               postgresql_using="currency::text::currency_type")

    # 2. 인덱스 원복
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        op.f('ix_unique_spatial_slot'), 
        'device_component_instances', 
        [
            sa.text("((spatial_context -> 'grid'::text) ->> 'row'::text)"), 
            sa.text("((spatial_context -> 'grid'::text) ->> 'col'::text)"), 
            sa.text("((spatial_context -> 'grid'::text) ->> 'layer'::text)")
        ], 
        unique=True
    )