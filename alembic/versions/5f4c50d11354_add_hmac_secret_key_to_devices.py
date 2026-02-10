"""add_hmac_secret_key_to_devices

Revision ID: 5f4c50d11354
Revises: f802b33b3b2b
Create Date: 2026-02-10 04:56:10.204059

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5f4c50d11354'
down_revision: Union[str, Sequence[str], None] = 'f802b33b3b2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# --- Enum 타입 정의 (DB에 없을 경우 자동 생성을 위해 필요) ---
device_visibility = postgresql.ENUM('PRIVATE', 'ORGANIZATION', 'PUBLIC', name='device_visibility')
device_status = postgresql.ENUM('PENDING', 'PROVISIONED', 'ONLINE', 'OFFLINE', 'TIMEOUT', 'RECOVERY_NEEDED', 'SAFETY_LOCKED', 'BLOCKED', name='device_status')
cluster_role = postgresql.ENUM('LEADER', 'FOLLOWER', name='cluster_role')

def upgrade() -> None:
    # 1. Enum 타입 체크 및 생성 (이미 있으면 건너뜀)
    device_visibility.create(op.get_bind(), checkfirst=True)
    device_status.create(op.get_bind(), checkfirst=True)
    cluster_role.create(op.get_bind(), checkfirst=True)

    # 2. devices 테이블에 hmac_secret_key 컬럼 추가
    op.add_column('devices', sa.Column('hmac_secret_key', sa.String(length=255), nullable=True))

    # 3. JSONB 인덱스 문제 해결 (Alembic의 무한 루프 방지용 고정 구문)
    # 기존 인덱스가 있다면 먼저 드롭한 뒤, 안정적인 리터럴 구문으로 생성합니다.
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.execute("""
        CREATE UNIQUE INDEX ix_unique_spatial_slot ON device_component_instances (
            ((spatial_context -> 'grid'::text) ->> 'row'::text),
            ((spatial_context -> 'grid'::text) ->> 'col'::text),
            ((spatial_context -> 'grid'::text) ->> 'layer'::text)
        )
    """)

def downgrade() -> None:
    # 1. 컬럼 삭제
    op.drop_column('devices', 'hmac_secret_key')

    # 2. 인덱스 복구
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.text("((spatial_context -> 'grid'::text) ->> 'row'::text)"), 
         sa.text("((spatial_context -> 'grid'::text) ->> 'col'::text)"), 
         sa.text("((spatial_context -> 'grid'::text) ->> 'layer'::text)")], 
        unique=True
    )
    
    # 주의: downgrade 시 Enum 타입 자체를 drop하는 것은 위험할 수 있으므로 
    # (다른 테이블에서 쓸 수 있음) 보통은 명시적으로 삭제하지 않는 것이 실전 원칙입니다.