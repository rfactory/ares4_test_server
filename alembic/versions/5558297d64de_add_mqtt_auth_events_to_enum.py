"""add_mqtt_auth_events_to_enum

Revision ID: <자동 생성된 ID>
Revises: 830ff77561df
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '<자동 생성된 ID>' # 파일명에 있는 ID로 유지하세요
down_revision: Union[str, Sequence[str], None] = '830ff77561df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # PostgreSQL에서는 트랜잭션 내부에서 Enum 값을 추가할 수 없는 경우가 많아
    # 트랜잭션을 일시적으로 커밋하고 실행하는 방식을 사용합니다.
    # (Alembic 설정에 따라 commit이 필요 없을 수도 있지만, 안전하게 처리)
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_log_event_type ADD VALUE IF NOT EXISTS 'MQTT_AUTH_SUCCESS'")
        op.execute("ALTER TYPE audit_log_event_type ADD VALUE IF NOT EXISTS 'MQTT_AUTH_FAILURE'")

def downgrade() -> None:
    # PostgreSQL에서 Enum 값 삭제는 매우 까다로우므로(데이터 무결성 문제)
    # 일반적으로 Downgrade에서는 아무 작업도 하지 않거나 무시합니다.
    pass