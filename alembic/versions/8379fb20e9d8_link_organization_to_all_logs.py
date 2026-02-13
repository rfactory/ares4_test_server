"""link_organization_to_all_logs

Revision ID: 8379fb20e9d8
Revises: 2c8fc092c48d
Create Date: 2026-02-13 04:44:50.910539

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '8379fb20e9d8'
down_revision: Union[str, Sequence[str], None] = '2c8fc092c48d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    def add_column_if_not_exists(table_name, column_name, column_type, fk_name=None):
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        if column_name not in columns:
            op.add_column(table_name, sa.Column(column_name, column_type, nullable=True))
            op.create_index(op.f(f'ix_{table_name}_{column_name}'), table_name, [column_name], unique=False)
            if fk_name:
                op.create_foreign_key(fk_name, table_name, 'organizations', [column_name], ['id'])
        else:
            # 컬럼은 있는데 인덱스나 FK가 없는 경우를 대비해 개별 체크 (필요시)
            pass

    # 1. alert_events
    add_column_if_not_exists('alert_events', 'organization_id', sa.BigInteger(), 'fk_alert_events_organization')

    # 2. audit_logs
    add_column_if_not_exists('audit_logs', 'organization_id', sa.BigInteger(), 'fk_audit_logs_organization')

    # 3. action_logs
    add_column_if_not_exists('action_logs', 'organization_id', sa.BigInteger(), 'fk_action_logs_organization')

    # 4. consumable_usage_logs
    add_column_if_not_exists('consumable_usage_logs', 'organization_id', sa.BigInteger(), 'fk_consumable_usage_logs_organization')

    # 5. firmware_updates
    add_column_if_not_exists('firmware_updates', 'initiated_by_organization_id', sa.BigInteger(), 'fk_firmware_updates_organization')

    # 6. provisioning_tokens
    add_column_if_not_exists('provisioning_tokens', 'issued_by_organization_id', sa.BigInteger(), 'fk_provisioning_tokens_organization')


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrade는 필요시 수동으로 컬럼 삭제 (안전상 pass 처리 가능)
    pass