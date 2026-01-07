from typing import Optional, List

from app.core.exceptions import ForbiddenError
from app.models.objects.user import User
from app.models.objects.role import Role

class T0GovernanceValidator:
    def validate(
        self, 
        *, 
        actor_user: User, 
        target_user: User, 
        roles_to_assign: Optional[List[Role]] = None,
        roles_to_revoke: Optional[List[Role]] = None
    ) -> None:
        """
        T0(tier=0) 역할들의 상호 견제 및 임명/해임 규칙을 검증합니다.
        """
        actor_roles = {r.role.name for r in actor_user.user_role_assignments if r.role.scope == 'SYSTEM'}
        
        roles_to_assign = roles_to_assign or []
        roles_to_revoke = roles_to_revoke or []

        # 1. System_Admin의 권한 규칙
        if "System_Admin" in actor_roles:
            # System_Admin은 오직 Prime_Admin 역할만 관리할 수 있음
            is_managing_only_prime_admin = True
            if any(r.name != "Prime_Admin" for r in roles_to_assign):
                is_managing_only_prime_admin = False
            if any(r.name != "Prime_Admin" for r in roles_to_revoke):
                is_managing_only_prime_admin = False
            
            if not is_managing_only_prime_admin:
                raise ForbiddenError("System_Admin can only assign or revoke the Prime_Admin role.")
            return # 허용

        # 2. Prime_Admin의 권한 규칙
        if "Prime_Admin" in actor_roles:
            # Prime_Admin은 System_Admin을 해임할 수 없음
            if any(r.name == "System_Admin" for r in roles_to_revoke):
                raise ForbiddenError("Prime_Admin cannot revoke the System_Admin role.")
            
            # Prime_Admin은 다른 사용자를 Prime_Admin으로 임명할 수 없음
            if any(r.name == "Prime_Admin" for r in roles_to_assign):
                raise ForbiddenError("Prime_Admin cannot assign another Prime_Admin role.")
            
            # 그 외의 경우는 허용 (System_Admin 임명, tier > 0 역할 관리)
            return # 허용

        # 3. T0 역할이 아닌 다른 역할이 T0 역할을 관리하려는 시도 방지
        is_managing_t0_role = any(r.tier == 0 for r in roles_to_assign) or any(r.tier == 0 for r in roles_to_revoke)
        if is_managing_t0_role:
            raise ForbiddenError("Only System_Admin or Prime_Admin can manage tier-0 roles.")

        # 일반적인 역할 관리 권한은 이 validator의 책임이 아님
        pass

t0_governance_validator = T0GovernanceValidator()
