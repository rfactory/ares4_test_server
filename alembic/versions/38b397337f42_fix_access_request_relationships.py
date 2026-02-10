"""fix_access_request_relationships

Revision ID: 38b397337f42
Revises: ab112e3e3b88
Create Date: 2026-02-06 04:47:39.255662

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '38b397337f42'
down_revision: Union[str, Sequence[str], None] = 'ab112e3e3b88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. 인덱스 안전하게 재생성
    # 기존 인덱스가 존재할 경우에만 삭제 (에러 방지)
    op.execute("DROP INDEX IF EXISTS ix_unique_spatial_slot")
    
    # 새로운 형식으로 인덱스 생성
    op.create_index(
        'ix_unique_spatial_slot', 
        'device_component_instances', 
        [sa.literal_column("(spatial_context->'grid'->>'row'), (spatial_context->'grid'->>'col'), (spatial_context->'grid'->>'layer')")], 
        unique=True
    )

    # 2. [추가] Enum 타입 체크 및 안전 장치
    # 만약 AccessRequest나 기타 테이블에서 사용하는 Enum이 에러를 일으킨다면 아래 패턴을 사용합니다.
    # 여기서는 예시로 작성해두었으니, 실제 에러나는 Enum 이름이 있다면 아래 주석을 풀고 사용하세요.
    """
    bind = op.get_bind()
    # 예: 'access_request_type'이라는 타입이 DB에 없을 때만 생성
    if not bind.dialect.has_type(bind, "access_request_type"):
        op.execute("CREATE TYPE access_request_type AS ENUM ('pull', 'push')")
    """

def downgrade() -> None:
    # 인덱스 원복
    op.drop_index('ix_unique_spatial_slot', table_name='device_component_instances')
    op.create_index(
        op.f('ix_unique_spatial_slot'), 
        'device_component_instances', 
        [
            sa.literal_column("((spatial_context -> 'grid'::text) ->> 'row'::text)"), 
            sa.literal_column("((spatial_context -> 'grid'::text) ->> 'col'::text)"), 
            sa.literal_column("((spatial_context -> 'grid'::text) ->> 'layer'::text)")
        ], 
        unique=True
    )