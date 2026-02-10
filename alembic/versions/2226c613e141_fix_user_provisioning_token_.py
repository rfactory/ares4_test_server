"""fix_user_provisioning_token_relationship_name
Revision ID: 2226c613e141
Revises: 8a712a4187c4
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '2226c613e141'
down_revision: Union[str, Sequence[str], None] = '8a712a4187c4'

def upgrade() -> None:
    # 1. Enum 타입 안전 생성 (이미 있으면 무시)
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'consumable_instance_status') THEN 
                CREATE TYPE consumable_instance_status AS ENUM ('ACTIVE', 'USED_UP', 'EXPIRED', 'DISCARDED'); 
            END IF;
        END $$;
    """)

    # 2. [핵심 수정] 명시적 캐스팅을 사용한 타입 변경
    # VARCHAR(50) -> Enum 타입으로 변환할 때 USING 구문 필수
    op.execute("""
        ALTER TABLE user_consumables 
        ALTER COLUMN status TYPE consumable_instance_status 
        USING status::text::consumable_instance_status;
    """)

    # 3. 인덱스 교정 (Expression Index 중복 방지)
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', 
                   [sa.literal_column("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
                   unique=True)

    # 4. 컬럼 주석 업데이트
    op.alter_column('telemetry_data', 'metric_name', comment='측정 항목명 (temp, co2 등)')
    op.alter_column('vision_features', 'vector_data', 
                   comment='추출된 벡터 또는 객체 인식 정보 (JSONB)',
                   existing_type=postgresql.JSONB(astext_type=sa.Text()))

def downgrade() -> None:
    # 다시 원복 시 (필요한 경우만)
    op.execute("ALTER TABLE user_consumables ALTER COLUMN status TYPE VARCHAR(50);")
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')