from typing import Any, Dict, Optional, List

from app.models.objects.user import User
from app.models.objects.role import Role
from app.core.redis_client import get_redis_client
from app.core.exceptions import ForbiddenError

class GovernanceValidator:
    def _check_conditions(
        self, 
        conditions: Dict[str, Any],
        **kwargs
    ) -> bool:
        """규칙의 모든 조건을 확인하고 충족하는지 여부를 반환합니다."""
        for condition_name, condition_value in conditions.items():
            checker_method = getattr(self, f"_check_{condition_name}", None)
            if not checker_method or not checker_method(value=condition_value, **kwargs):
                return False
        return True

    def _check_check_max_headcount(self, value: bool, **kwargs) -> bool:
        """역할의 최대 인원수를 확인합니다."""
        if not value: return True
        target_role = kwargs.get('target_role')
        current_headcount = kwargs.get('current_headcount')

        if not target_role or target_role.max_headcount is None or target_role.max_headcount == -1:
            return True
        
        return current_headcount < target_role.max_headcount

    def _check_prime_admin_count(self, value: Dict[str, int], **kwargs) -> bool:
        """Prime_Admin 역할의 현재 인원수를 확인합니다."""
        prime_admin_count = kwargs.get('prime_admin_count')
        if prime_admin_count is None: return False
        
        for operator, num in value.items():
            if operator == "$gt" and not prime_admin_count > num:
                return False
            if operator == "$lt" and not prime_admin_count < num:
                return False
        return True

    def _check_target_role_tier(self, value: Dict[str, int], **kwargs) -> bool:
        """대상 역할의 티어를 확인합니다."""
        target_role = kwargs.get('target_role')
        if not target_role or target_role.tier is None: return False
        
        for operator, num in value.items():
            if operator == "$gt" and not target_role.tier > num:
                return False
            if operator == "$lt" and not target_role.tier < num:
                return False
        return True

    def _check_target_role_scope(self, value: str, **kwargs) -> bool:
        """대상 역할의 스코프를 확인합니다."""
        target_role = kwargs.get('target_role')
        if not target_role: return False
        return target_role.scope == value

    def _check_is_emergency_mode(self, value: bool, **kwargs) -> bool:
        """비상 모드 활성화 여부를 확인합니다."""
        redis_client = get_redis_client()
        is_emergency = redis_client.get('system:emergency_mode_active') == b'true'
        return is_emergency if value else not is_emergency

    def evaluate_rule(
        self,
        *,
        actor_user: User,
        matching_rules: List[Any], # 실제로는 GovernanceRule 리스트
        **kwargs
    ) -> None:
        """전달된 규칙 목록을 평가하여 허용 여부를 결정하고, 실패 시 에러를 발생시킵니다."""
        actor_roles: List[Role] = [assignment.role for assignment in actor_user.user_role_assignments if assignment.role]
        
        allow_action = False

        for rule in matching_rules:
            if rule.actor_role_id not in [role.id for role in actor_roles]:
                continue

            if rule.conditions and not self._check_conditions(conditions=rule.conditions, actor_user=actor_user, **kwargs):
                continue
            
            if rule.allow:
                allow_action = True
                break 
            else:
                raise ForbiddenError(f"Action forbidden by governance rule: {rule.rule_name}")

        if not allow_action:
            raise ForbiddenError("No governance rule allows this action.")


governance_validator = GovernanceValidator()
