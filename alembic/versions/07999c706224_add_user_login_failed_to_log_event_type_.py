"""Add USER_LOGIN_FAILED to log_event_type enum

Revision ID: 07999c706224
Revises: 189596bcd706
Create Date: 2026-01-09 00:54:29.938642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07999c706224'
down_revision: Union[str, Sequence[str], None] = '189596bcd706'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE log_event_type ADD VALUE 'USER_LOGIN_FAILED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Enum 값 삭제는 Postgres 10+에서 ALTER TYPE ... DROP VALUE IF EXISTS를 사용해야 합니다.
    # 하지만 기존 데이터를 참조하는 경우 에러가 발생할 수 있습니다.
    # 따라서 enum 값을 참조하는 모든 컬럼의 해당 값을 먼저 NULL로 변경하거나, 더 보수적인 접근 방식이 필요합니다.
    # 여기서는 간단히 제거하는 방식으로 작성합니다.
    op.execute("ALTER TYPE log_event_type REMOVE VALUE 'USER_LOGIN_FAILED'")
