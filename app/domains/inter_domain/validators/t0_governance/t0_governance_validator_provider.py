from typing import Optional, List

from app.models.objects.user import User
from app.models.objects.role import Role
from app.domains.action_authorization.validators.t0_governance.t0_governance_validator import t0_governance_validator

class T0GovernanceValidatorProvider:
    def validate(
        self, 
        *, 
        actor_user: User, 
        target_user: User, 
        roles_to_assign: Optional[List[Role]] = None,
        roles_to_revoke: Optional[List[Role]] = None
    ) -> None:
        """
        T0 거버넌스 규칙 검증을 실행합니다.
        """
        return t0_governance_validator.validate(
            actor_user=actor_user,
            target_user=target_user,
            roles_to_assign=roles_to_assign,
            roles_to_revoke=roles_to_revoke
        )

t0_governance_validator_provider = T0GovernanceValidatorProvider()
