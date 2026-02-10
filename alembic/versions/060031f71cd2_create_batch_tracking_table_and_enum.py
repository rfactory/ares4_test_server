"""create_batch_tracking_table_and_enum
Revision ID: 060031f71cd2
Revises: 8b7d829af95f
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '060031f71cd2'
down_revision: Union[str, Sequence[str], None] = '8b7d829af95f'

def upgrade() -> None:
    # 1. batch_tracking_status Enum 안전하게 생성
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'batch_tracking_status') THEN 
                CREATE TYPE batch_tracking_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'); 
            END IF; 
        END $$;
    """)

    # 2. BatchTracking 테이블 생성
    op.create_table('batch_trackings',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('batch_id', sa.String(length=50), nullable=False, comment='배치 고유 식별자 (UUID)'),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('processed_count', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 
                                          name='batch_tracking_status', create_type=False), 
                  nullable=False, comment='진행 상태'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('device_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_batch_trackings_batch_id'), 'batch_trackings', ['batch_id'], unique=True)
    op.create_index(op.f('ix_batch_trackings_id'), 'batch_trackings', ['id'], unique=False)

    # 3. Enum 타입 이름 변경 및 존재 여부 체크 (방어적 로직)
    # 기존 타입(old)이 존재하고 새 타입(new)이 존재하지 않을 때만 RENAME 수행
    op.execute("""
        DO $$ 
        BEGIN 
            -- componentsourcetype -> component_source_type
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'componentsourcetype') AND 
               NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'component_source_type') THEN
                ALTER TYPE componentsourcetype RENAME TO component_source_type;
            END IF;

            -- controltype -> control_type
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'controltype') AND 
               NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'control_type') THEN
                ALTER TYPE controltype RENAME TO control_type;
            END IF;
        END $$;
    """)

    # 4. 컬럼 타입 캐스팅 (이미 처리되었을 수 있으므로 예외 처리 고려)
    # 이 부분은 테이블 구조가 이미 새 타입을 바라보고 있다면 무시되도록 SQL로 작성
    op.execute("""
        ALTER TABLE internal_system_unit_physical_components 
        ALTER COLUMN source_type TYPE component_source_type 
        USING source_type::text::component_source_type;
    """)
    op.execute("""
        ALTER TABLE supported_components 
        ALTER COLUMN control_type TYPE control_type 
        USING control_type::text::control_type;
    """)

    # 5. 기타 코멘트 및 인덱스 업데이트
    op.alter_column('vision_features', 'vector_data', comment='추출된 벡터 또는 객체 인식 정보 (JSONB)')
    
    # 인덱스 교정 (기존 인덱스가 있으면 삭제 후 재생성)
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    op.create_index('ix_unique_spatial_slot', 'device_component_instances', 
                   [sa.literal_column("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))")], 
                   unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_batch_trackings_id'), table_name='batch_trackings')
    op.drop_index(op.f('ix_batch_trackings_batch_id'), table_name='batch_trackings')
    op.drop_table('batch_trackings')