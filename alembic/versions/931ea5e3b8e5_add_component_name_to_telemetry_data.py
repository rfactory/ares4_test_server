"""Add component_name to telemetry_data

Revision ID: 931ea5e3b8e5
Revises: 4f0c135f2327
Create Date: 2026-02-11 02:57:29.918017

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '931ea5e3b8e5'
down_revision: Union[str, Sequence[str], None] = '4f0c135f2327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # 1. [노이즈 제거] device_component_instances 관련 인덱스 수정 코드는 
    # Alembic의 JSONB 오인식으로 인한 것이므로 제거하고 telemetry_data에만 집중합니다.

    # 2. telemetry_data 테이블에 component_name 컬럼 추가
    # [주의] 기존 데이터가 있을 경우를 대비해 'main_board'를 기본값으로 설정하여 
    # NOT NULL 제약 조건 위반을 방지합니다.
    op.add_column('telemetry_data', 
        sa.Column('component_name', sa.String(length=100), 
                  nullable=False, 
                  server_default='main_board',
                  comment='데이터가 발생한 부품 인스턴스 명칭')
    )

    # 3. 유니크 제약 조건 생성 (CRUD의 bulk_upsert가 작동하기 위한 핵심 장치)
    op.create_unique_constraint(
        '_device_component_metric_time_uc', 
        'telemetry_data', 
        ['device_id', 'component_name', 'metric_name', 'captured_at']
    )

    # 4. 조회 성능을 위한 인덱스 생성
    op.create_index(
        op.f('ix_telemetry_data_component_name'), 
        'telemetry_data', 
        ['component_name'], 
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 생성 역순으로 제거
    op.drop_index(op.f('ix_telemetry_data_component_name'), table_name='telemetry_data')
    op.drop_constraint('_device_component_metric_time_uc', 'telemetry_data', type_='unique')
    op.drop_column('telemetry_data', 'component_name')