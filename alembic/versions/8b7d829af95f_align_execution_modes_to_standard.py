"""align_execution_modes_to_standard

Revision ID: 8b7d829af95f
Revises: 38b397337f42
Create Date: 2026-02-06 08:01:45.325874

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8b7d829af95f'
down_revision: Union[str, Sequence[str], None] = '38b397337f42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. 신규 ENUM 타입 생성 (기존에 없을 경우만 생성)
    op.execute("DO $$ BEGIN CREATE TYPE access_request_type AS ENUM ('PULL', 'PUSH'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE access_request_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE cluster_role AS ENUM ('LEADER', 'FOLLOWER'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE execution_mode AS ENUM ('ONCE', 'CONTINUOUS', 'INTERVAL', 'CRON'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE concurrency_policy AS ENUM ('SKIP', 'FORCED', 'REPLACE', 'QUEUE'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE observation_snapshot_type AS ENUM ('IMAGE', 'SENSOR', 'LOG', 'ALARM', 'COMMAND'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE consumable_instance_status AS ENUM ('ACTIVE', 'USED_UP', 'EXPIRED', 'DISCARDED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE component_source_type AS ENUM ('INITIAL', 'WARRANTY', 'PAID_REPAIR', 'DIY_REPLACEMENT'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE consumable_log_event_type AS ENUM ('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # 2. [devices] cluster_role 수정 (에러 해결 핵심)
    op.execute("ALTER TABLE devices ALTER COLUMN cluster_role DROP DEFAULT")
    op.execute("ALTER TABLE devices ALTER COLUMN cluster_role TYPE cluster_role USING cluster_role::cluster_role")
    op.execute("ALTER TABLE devices ALTER COLUMN cluster_role SET DEFAULT 'FOLLOWER'::cluster_role")

    # 3. [schedules] execution_mode & concurrency_policy 수정 (값 매핑 포함)
    op.execute("ALTER TABLE schedules ALTER COLUMN execution_mode DROP DEFAULT")
    op.execute("ALTER TABLE schedules ALTER COLUMN concurrency_policy DROP DEFAULT")
    op.execute("""
        ALTER TABLE schedules 
        ALTER COLUMN execution_mode TYPE execution_mode 
        USING (CASE 
            WHEN execution_mode::text = 'SET' THEN 'ONCE'::execution_mode 
            WHEN execution_mode::text = 'INFINITE' THEN 'CONTINUOUS'::execution_mode 
            ELSE execution_mode::text::execution_mode 
        END),
        ALTER COLUMN concurrency_policy TYPE concurrency_policy 
        USING concurrency_policy::text::concurrency_policy
    """)
    op.execute("ALTER TABLE schedules ALTER COLUMN execution_mode SET DEFAULT 'ONCE'::execution_mode")
    op.execute("ALTER TABLE schedules ALTER COLUMN concurrency_policy SET DEFAULT 'SKIP'::concurrency_policy")

    # 4. [trigger_rules]
    op.execute("ALTER TABLE trigger_rules ALTER COLUMN execution_mode DROP DEFAULT")
    op.execute("ALTER TABLE trigger_rules ALTER COLUMN concurrency_policy DROP DEFAULT")
    op.execute("""
        ALTER TABLE trigger_rules 
        ALTER COLUMN execution_mode TYPE execution_mode 
        USING (CASE 
            WHEN execution_mode::text = 'SET' THEN 'ONCE'::execution_mode 
            WHEN execution_mode::text = 'INFINITE' THEN 'CONTINUOUS'::execution_mode 
            ELSE execution_mode::text::execution_mode 
        END),
        ALTER COLUMN concurrency_policy TYPE concurrency_policy 
        USING concurrency_policy::text::concurrency_policy
    """)
    op.execute("ALTER TABLE trigger_rules ALTER COLUMN execution_mode SET DEFAULT 'ONCE'::execution_mode")
    op.execute("ALTER TABLE trigger_rules ALTER COLUMN concurrency_policy SET DEFAULT 'REPLACE'::concurrency_policy")

    # 5. [access_requests]
    op.execute("""
        ALTER TABLE access_requests 
        ALTER COLUMN type TYPE access_request_type USING type::access_request_type,
        ALTER COLUMN status TYPE access_request_status USING status::access_request_status
    """)

    # 6. [observation_snapshots]
    op.execute("""
        ALTER TABLE observation_snapshots 
        ALTER COLUMN observation_type TYPE observation_snapshot_type USING observation_type::text::observation_snapshot_type
    """)

    # 7. [vision_features] JSON -> JSONB
    op.execute("ALTER TABLE vision_features ALTER COLUMN vector_data TYPE JSONB USING vector_data::jsonb")
    op.create_index(op.f('ix_vision_features_model_version'), 'vision_features', ['model_version'], unique=False)

    # 8. 수치 데이터 및 기타 인덱스
    op.execute("ALTER TABLE subscription_plans ALTER COLUMN price_monthly TYPE NUMERIC(10, 2)")
    op.execute("ALTER TABLE subscription_plans ALTER COLUMN price_yearly TYPE NUMERIC(10, 2)")
    op.create_index(op.f('ix_subscription_plan_features_feature_key'), 'subscription_plan_features', ['feature_key'], unique=False)

    # [device_component_instances] 복합 인덱스 재구성
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.execute("""
        CREATE UNIQUE INDEX ix_unique_spatial_slot ON device_component_instances 
        ((spatial_context->'grid'->>'row'), (spatial_context->'grid'->>'col'), (spatial_context->'grid'->>'layer'))
    """)

    # 9. 코멘트 정리
    op.execute("COMMENT ON COLUMN observation_snapshots.id IS '고유 스냅샷 ID'")
    op.execute("COMMENT ON COLUMN schedules.end_time IS 'NULL일 경우 무한 지속(Continuous) 또는 영구 반복을 의미함'")

def downgrade() -> None:
    # 실무적으로 ENUM에서 VARCHAR로 되돌리는 로직은 매우 복잡하므로 pass 처리하거나 
    # 필요시 각 테이블의 컬럼을 VARCHAR로 다시 캐스팅하는 로직을 추가합니다.
    pass