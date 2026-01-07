from sqlalchemy.orm import Session
from typing import List

from app.domains.services.governance.services.governance_command_service import governance_command_service
from app.core.redis_client import get_redis_client
from app.models.objects.role import Role
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider

class GovernanceCommandProvider:
    EMERGENCY_MODE_KEY = governance_command_service.EMERGENCY_MODE_KEY

    def check_and_update_emergency_mode(self, db: Session, *, roles_changed: List[Role]):
        """Policy로부터 변경된 역할 목록을 받아 비상 모드 상태를 확인하고 업데이트합니다."""
        if any(role.name == "Prime_Admin" for role in roles_changed):
            prime_admin_count = governance_query_provider.get_prime_admin_count(db)
            self.update_emergency_mode(prime_admin_count=prime_admin_count)

    def update_emergency_mode(self, *, prime_admin_count: int):
        """Prime Admin 숫자를 기반으로 비상 모드 상태를 업데이트합니다."""
        redis_client = get_redis_client()
        return governance_command_service.update_emergency_mode(
            redis_client=redis_client, 
            prime_admin_count=prime_admin_count
        )

governance_command_provider = GovernanceCommandProvider()
