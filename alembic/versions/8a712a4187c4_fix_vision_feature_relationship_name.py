"""fix_vision_feature_relationship_name
Revision ID: 8a712a4187c4
Revises: 060031f71cd2
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8a712a4187c4'
down_revision: Union[str, Sequence[str], None] = '060031f71cd2'

def upgrade() -> None:
    # 1. Enum 타입 중복 체크 및 안전 생성 로직
    op.execute("""
        DO $$ 
        BEGIN 
            -- batch_tracking_status 생성
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'batch_tracking_status') THEN 
                CREATE TYPE batch_tracking_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'); 
            END IF;
            
            -- consumable_log_event_type 생성
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'consumable_log_event_type') THEN 
                CREATE TYPE consumable_log_event_type AS ENUM (
                    'DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 
                    'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW'
                ); 
            END IF;

            -- consumable_instance_status 생성
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'consumable_instance_status') THEN 
                CREATE TYPE consumable_instance_status AS ENUM ('ACTIVE', 'USED_UP', 'EXPIRED', 'DISCARDED'); 
            END IF;
        END $$;
    """)

    # 2. 컬럼 타입 변경 및 캐스팅 (Enum Mismatch 해결)
    # 기존 log_event_type에서 새로운 consumable_log_event_type으로 캐스팅
    op.execute("""
        ALTER TABLE consumable_usage_logs 
        ALTER COLUMN event_type TYPE consumable_log_event_type 
        USING event_type::text::consumable_log_event_type;
    """)

    # 3. 인덱스 교정 (Expression Index)
    # 기존 인덱스 삭제 후 더 명확한 경로로 재생성
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', 
                   [sa.literal_column("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
                   unique=True)

    # 4. 기타 스키마 코멘트 및 길이 변경
    op.alter_column('roles', 'lineage', type_=sa.String(length=255))
    
    # 5. 컬럼 주석(Comment) 일제 정비 (Any 타입을 방지하기 위한 메타데이터)
    op.alter_column('internal_asset_purchase_records', 'quantity', comment='구매 수량')
    op.alter_column('internal_asset_purchase_records', 'purchase_price_per_unit', comment='단가')
    op.alter_column('telemetry_data', 'std_dev', comment='안정성 지표')
    op.alter_column('vision_features', 'vector_data', comment='추출된 벡터 또는 객체 인식 정보 (JSONB)')

def downgrade() -> None:
    # 롤백 로직 (필요 시 작성)
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.execute("DROP TYPE IF EXISTS consumable_log_event_type")
    op.execute("DROP TYPE IF EXISTS batch_tracking_status")