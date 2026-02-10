"""move_logic_to_system_unit_and_add_control_fields

Revision ID: ab112e3e3b88
Revises: 219f05df0ce4
Create Date: 2026-02-05 05:13:23.885090

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ab112e3e3b88'
down_revision: Union[str, Sequence[str], None] = '219f05df0ce4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. PostgreSQL Enum 타입 정의 및 생성 (이미 존재하면 건너뜀)
    execution_mode_enum = sa.Enum('INFINITE', 'SET', 'INTERVAL', name='executionmode')
    concurrency_policy_enum = sa.Enum('SKIP', 'REPLACE', 'QUEUE', name='concurrencypolicy')
    
    execution_mode_enum.create(op.get_bind(), checkfirst=True)
    concurrency_policy_enum.create(op.get_bind(), checkfirst=True)

    # 2. 기존 인덱스 수정 (공간 정보 관련)
    op.drop_index(op.f('ix_unique_spatial_slot'), table_name='device_component_instances')
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', 
                   [sa.literal_column("(spatial_context->'grid'->>'row'), (spatial_context->'grid'->>'col'), (spatial_context->'grid'->>'layer')")], 
                   unique=True)

    # --- [Schedules 테이블 작업] ---
    # 3-1. 신규 컬럼들을 먼저 nullable=True로 추가
    op.add_column('schedules', sa.Column('priority', sa.Integer(), nullable=True))
    op.add_column('schedules', sa.Column('execution_mode', execution_mode_enum, nullable=True))
    op.add_column('schedules', sa.Column('is_locked', sa.Boolean(), nullable=True))
    op.add_column('schedules', sa.Column('logic_version', sa.String(length=50), nullable=True))
    op.add_column('schedules', sa.Column('timeout_seconds', sa.Integer(), nullable=True))
    op.add_column('schedules', sa.Column('concurrency_policy', concurrency_policy_enum, nullable=True))
    op.add_column('schedules', sa.Column('system_unit_id', sa.BigInteger(), nullable=True))

    # 3-2. 기존 데이터 업데이트 및 기기 소속 정보를 시스템 유닛으로 이관
    # (이미 연결된 device_id를 통해 system_unit_id를 찾아 매칭합니다)
    op.execute("""
        UPDATE schedules 
        SET priority = 10, 
            execution_mode = 'INTERVAL', 
            is_locked = False, 
            logic_version = '1.0.0', 
            concurrency_policy = 'SKIP',
            system_unit_id = (SELECT system_unit_id FROM devices WHERE devices.id = schedules.device_id)
    """)

    # 3-3. 필수 컬럼들에 대해 NOT NULL 제약 조건 적용
    op.alter_column('schedules', 'priority', nullable=False)
    op.alter_column('schedules', 'execution_mode', nullable=False)
    op.alter_column('schedules', 'is_locked', nullable=False)
    op.alter_column('schedules', 'logic_version', nullable=False)
    op.alter_column('schedules', 'concurrency_policy', nullable=False)
    # system_unit_id가 없는 데이터가 있을 수 있으므로 여기서는 체크 후 적용하거나 유지
    op.execute("UPDATE schedules SET system_unit_id = 1 WHERE system_unit_id IS NULL") # 임시 방편
    op.alter_column('schedules', 'system_unit_id', nullable=False)

    # 3-4. 관계 정리 (Device FK 삭제, SystemUnit FK 추가)
    op.create_index(op.f('ix_schedules_system_unit_id'), 'schedules', ['system_unit_id'], unique=False)
    op.drop_constraint('schedules_device_id_fkey', 'schedules', type_='foreignkey')
    op.create_foreign_key(None, 'schedules', 'system_units', ['system_unit_id'], ['id'])
    op.drop_column('schedules', 'device_id')


    # --- [Trigger Rules 테이블 작업] ---
    # 4-1. 컬럼 추가
    op.add_column('trigger_rules', sa.Column('priority', sa.Integer(), nullable=True))
    op.add_column('trigger_rules', sa.Column('execution_mode', execution_mode_enum, nullable=True))
    op.add_column('trigger_rules', sa.Column('is_locked', sa.Boolean(), nullable=True))
    op.add_column('trigger_rules', sa.Column('logic_version', sa.String(length=50), nullable=True))
    op.add_column('trigger_rules', sa.Column('timeout_seconds', sa.Integer(), nullable=True))
    op.add_column('trigger_rules', sa.Column('concurrency_policy', concurrency_policy_enum, nullable=True))
    op.add_column('trigger_rules', sa.Column('system_unit_id', sa.BigInteger(), nullable=True))

    # 4-2. 데이터 업데이트
    op.execute("""
        UPDATE trigger_rules 
        SET priority = 50, 
            execution_mode = 'SET', 
            is_locked = False, 
            logic_version = '1.0.0', 
            concurrency_policy = 'REPLACE',
            system_unit_id = (SELECT system_unit_id FROM devices WHERE devices.id = trigger_rules.device_id)
    """)

    # 4-3. NOT NULL 적용
    op.alter_column('trigger_rules', 'priority', nullable=False)
    op.alter_column('trigger_rules', 'execution_mode', nullable=False)
    op.alter_column('trigger_rules', 'is_locked', nullable=False)
    op.alter_column('trigger_rules', 'logic_version', nullable=False)
    op.alter_column('trigger_rules', 'concurrency_policy', nullable=False)
    op.execute("UPDATE trigger_rules SET system_unit_id = 1 WHERE system_unit_id IS NULL")
    op.alter_column('trigger_rules', 'system_unit_id', nullable=False)

    # 4-4. 관계 정리
    op.create_index(op.f('ix_trigger_rules_system_unit_id'), 'trigger_rules', ['system_unit_id'], unique=False)
    op.drop_constraint('trigger_rules_device_id_fkey', 'trigger_rules', type_='foreignkey')
    op.create_foreign_key(None, 'trigger_rules', 'system_units', ['system_unit_id'], ['id'])
    op.drop_column('trigger_rules', 'device_id')


def downgrade() -> None:
    # 역순으로 복구 로직 작성 (생략하거나 필요한 경우 추가)
    pass