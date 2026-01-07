from sqlalchemy.orm import Session
from typing import Optional, List, Any

from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.governance import GovernanceRule # GovernanceRule 임포트 추가
from app.domains.action_authorization.validators.governance.governance_validator import governance_validator

class GovernanceValidatorProvider:
    def evaluate_rule(
        self,
        *,
        actor_user: User,
        matching_rules: List[GovernanceRule], # GovernanceRule 리스트로 타입 명시
        **kwargs
    ) -> None: # Validator는 실패 시 에러를 발생시키므로 반환값 없음
        governance_validator.evaluate_rule(
            actor_user=actor_user,
            matching_rules=matching_rules,
            **kwargs
        )

governance_validator_provider = GovernanceValidatorProvider()
