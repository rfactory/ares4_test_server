from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.domains.services.governance.services.governance_query_service import governance_query_service
from app.domains.services.governance.crud.governance_crud import governance_rule_crud
from app.models.objects.user import User
from app.models.objects.role import Role

class GovernanceQueryProvider:
    def get_prime_admin_count(self, db: Session) -> int:
        """Prime Admin 역할의 현재 사용자 수를 조회합니다."""
        return governance_query_service.get_prime_admin_count(db)

    def get_matching_rules(
        self,
        db: Session,
        *,
        actor_user: User,
        action: str,
        context: str,
        target_role: Optional[Role] = None
    ) -> List[Any]: # List[GovernanceRule]을 반환
        """주어진 조건에 맞는 거버넌스 규칙 목록을 조회합니다."""
        # Policy에서 actor_user 객체만 넘겨받아 내부적으로 actor_role_id를 추출합니다.
        actor_role_id = actor_user.user_role_assignments[0].role_id if actor_user.user_role_assignments else None
        if not actor_role_id: return []

        target_role_id = target_role.id if target_role else None

        return governance_rule_crud.find_matching_rules(
            db=db,
            actor_role_id=actor_role_id,
            action=action,
            context=context,
            target_role_id=target_role_id
        )

governance_query_provider = GovernanceQueryProvider()
