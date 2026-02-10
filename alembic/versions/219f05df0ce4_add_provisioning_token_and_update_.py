"""Add provisioning token and update device status

Revision ID: 219f05df0ce4
Revises: 5bf14c607614
Create Date: 2026-02-03 09:20:42.776195

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '219f05df0ce4'
down_revision: Union[str, Sequence[str], None] = '5bf14c607614'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    # 1. ENUM 타입 처리 (존재 여부 확인 후 생성)
    type_exists = conn.execute(sa.text(
        "SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
        "WHERE t.typname = 'audit_log_event_type'"
    )).scalar()

    if not type_exists:
        audit_log_event_type = postgresql.ENUM(
            'DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED',
            'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW',
            'SERVER_CERTIFICATE_REUSED', 'ORGANIZATION_CREATED', 'ORGANIZATION_UPDATED',
            'ORGANIZATION_DELETED', 'ACCESS_REQUEST_CREATED', 'ACCESS_REQUEST_UPDATED',
            'ACCESS_REQUEST_DELETED', 'USER_ROLE_ASSIGNED', 'USER_ROLE_REVOKED', 'USER_LOGIN_FAILED',
            name='audit_log_event_type'
        )
        audit_log_event_type.create(conn)

    # device_status ENUM 값 추가 (IF NOT EXISTS 사용으로 중복 방지)
    op.execute("COMMIT") 
    for status in ['PENDING', 'PROVISIONED', 'BLOCKED']:
        op.execute(sa.text(f"ALTER TYPE device_status ADD VALUE IF NOT EXISTS '{status}'"))

    # 2. 테이블 생성 (존재하지 않을 때만 실행)
    if 'provisioning_tokens' not in tables:
        op.create_table('provisioning_tokens',
            sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
            sa.Column('device_id', sa.BigInteger(), nullable=False),
            sa.Column('token_value', sa.String(length=255), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_used', sa.Boolean(), nullable=False),
            sa.Column('issued_by_user_id', sa.BigInteger(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
            sa.ForeignKeyConstraint(['issued_by_user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('device_id')
        )
        op.create_index(op.f('ix_provisioning_tokens_id'), 'provisioning_tokens', ['id'], unique=False)
        op.create_index(op.f('ix_provisioning_tokens_token_value'), 'provisioning_tokens', ['token_value'], unique=True)

    # 3. 컬럼 타입 변경 (현재 타입을 확인 후 필요 시에만 변경)
    current_type = conn.execute(sa.text(
        "SELECT udt_name FROM information_schema.columns "
        "WHERE table_name = 'audit_logs' AND column_name = 'event_type'"
    )).scalar()
    
    if current_type != 'audit_log_event_type':
        op.execute("ALTER TABLE audit_logs ALTER COLUMN event_type TYPE audit_log_event_type USING event_type::text::audit_log_event_type")

    # 4. devices 테이블 컬럼 추가 (각 컬럼별 존재 여부 확인)
    device_columns = [col['name'] for col in inspector.get_columns('devices')]
    if 'cluster_role' not in device_columns:
        op.add_column('devices', sa.Column('cluster_role', sa.String(length=50), server_default='FOLLOWER', nullable=False))
    if 'logical_index' not in device_columns:
        op.add_column('devices', sa.Column('logical_index', sa.Integer(), nullable=True))
    if 'replaced_from_id' not in device_columns:
        op.add_column('devices', sa.Column('replaced_from_id', sa.BigInteger(), nullable=True))
        op.create_foreign_key('fk_devices_replaced_from', 'devices', 'devices', ['replaced_from_id'], ['id'])

    # 5. 인덱스 및 코멘트 정리
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', [sa.literal_column("(spatial_context->'grid'->>'row'), (spatial_context->'grid'->>'col'), (spatial_context->'grid'->>'layer')")], unique=True)
    op.execute("COMMENT ON COLUMN observation_snapshots.observation_type IS '데이터 정체성이 명확하지 않은 요청은 DB 수준에서 거부합니다.'")

def downgrade() -> None:
    # Downgrade 로직
    op.execute("COMMENT ON COLUMN observation_snapshots.observation_type IS NULL")
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(op.f('ix_unique_spatial_slot'), 'device_component_instances', [sa.literal_column("((spatial_context -> 'grid'::text) ->> 'row'::text)"), sa.literal_column("((spatial_context -> 'grid'::text) ->> 'col'::text)"), sa.literal_column("((spatial_context -> 'grid'::text) ->> 'layer'::text)")], unique=True)
    op.drop_constraint('fk_devices_replaced_from', 'devices', type_='foreignkey')
    op.drop_column('devices', 'replaced_from_id')
    op.drop_column('devices', 'logical_index')
    op.drop_column('devices', 'cluster_role')
    op.drop_index(op.f('ix_provisioning_tokens_token_value'), table_name='provisioning_tokens')
    op.drop_index(op.f('ix_provisioning_tokens_id'), table_name='provisioning_tokens')
    op.drop_table('provisioning_tokens')