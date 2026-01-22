"""Final Safe Master Recovery Migration

Revision ID: 5c245488e302
Revises: 8c13b540a9a4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '5c245488e302'
down_revision = '8c13b540a9a4'

def upgrade() -> None:
    conn = op.get_bind()

    # 1. 신규 테이블 생성 (존재하지 않는 것만 생성)
    new_tables = [
        ('device_roles', sa.Column('id', sa.BigInteger(), primary_key=True), 
         sa.Column('role_key', sa.String(50), nullable=False, unique=True),
         sa.Column('display_name', sa.String(100), nullable=False)),
        
        ('system_units', sa.Column('id', sa.BigInteger(), primary_key=True),
         sa.Column('name', sa.String(100), nullable=False),
         sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'PROVISIONING', name='unit_status'), nullable=False),
         sa.Column('organization_id', sa.BigInteger(), nullable=False)),
         
        ('action_logs', sa.Column('id', sa.BigInteger(), primary_key=True),
         sa.Column('actor_type', sa.Enum('USER', 'RL_AGENT', 'LLM_MCP', 'SYSTEM', name='actor_type'), nullable=False),
         sa.Column('command', sa.String(100), nullable=False),
         sa.Column('status', sa.Enum('REQUESTED', 'SUCCESS', 'FAILED', 'TIMEOUT', name='action_status'), nullable=False),
         sa.Column('device_id', sa.BigInteger(), nullable=False),
         sa.Column('system_unit_id', sa.BigInteger(), nullable=False)),

        ('unit_activity_logs', sa.Column('id', sa.BigInteger(), primary_key=True),
         sa.Column('activity_type', sa.Enum('OPERATION', 'INFERENCE', 'MAINTENANCE', 'SYSTEM_EVENT', name='unit_activity_type'), nullable=False),
         sa.Column('system_unit_id', sa.BigInteger(), nullable=True)),

        ('image_registries', sa.Column('id', sa.BigInteger(), primary_key=True),
         sa.Column('storage_path', sa.String(500), nullable=False),
         sa.Column('device_id', sa.BigInteger(), nullable=False),
         sa.Column('system_unit_id', sa.BigInteger(), nullable=False)),

        ('vision_features', sa.Column('id', sa.BigInteger(), primary_key=True),
         sa.Column('image_id', sa.BigInteger(), nullable=False),
         sa.Column('vector_data', sa.JSON(), nullable=False),
         sa.Column('device_id', sa.BigInteger(), nullable=False))
    ]

    for table_name, *cols in new_tables:
        if not conn.dialect.has_table(conn, table_name):
            op.create_table(table_name, *cols)

    # 2. BigInteger 변환 (이미 bigint인 경우 건너뜀)
    tables_to_alter = ['users', 'devices', 'organizations', 'roles', 'permissions', 'refresh_tokens']
    for table in tables_to_alter:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id TYPE BIGINT USING id::bigint")

    # 3. refresh_tokens 컬럼 추가 (존재 여부 체크)
    res = conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='refresh_tokens' AND column_name='created_at'"))
    if not res.first():
        op.add_column('refresh_tokens', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
        op.add_column('refresh_tokens', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    
    # 4. devices에 system_unit_id 추가 (존재 여부 체크)
    res = conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='devices' AND column_name='system_unit_id'"))
    if not res.first():
        op.add_column('devices', sa.Column('system_unit_id', sa.BigInteger(), nullable=True))

def downgrade() -> None:
    pass