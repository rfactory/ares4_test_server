from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.objects.user import User
from app.models.objects.role import Role

# Inter-Domain Provider Imports
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.validators.governance.governance_validator_provider import governance_validator_provider
from app.domains.inter_domain.validators.headcount.headcount_validator_provider import headcount_validator_provider

class GetAssignableRolesPolicy:
    """
    [Policy]
    현재 사용자가 특정 컨텍스트에서 할당할 수 있는 역할 목록을 결정하는 오케스트레이터입니다.
    """
    def execute(self, db: Session, *, actor_user: User, organization_id: Optional[int]) -> List[Role]:
        assignable_roles = []
        accessible_roles = role_query_provider.get_accessible_roles(db, actor_user=actor_user, organization_id=organization_id)
        prime_admin_count = governance_query_provider.get_prime_admin_count(db)

        for role in accessible_roles:
            try:
                matching_rules = governance_query_provider.get_matching_rules(
                    db, actor_user=actor_user, action="assign_role", context=role.scope, target_role=role
                )
                current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=role.id)
                
                governance_validator_provider.evaluate_rule(
                    actor_user=actor_user,
                    matching_rules=matching_rules,
                    target_role=role,
                    current_headcount=current_headcount,
                    prime_admin_count=prime_admin_count
                )
                
                headcount_validator_provider.validate(
                    role_name=role.name,
                    current_headcount=current_headcount,
                    max_headcount=role.max_headcount
                )
                
                assignable_roles.append(role)

            except Exception:
                continue

        return assignable_roles

get_assignable_roles_policy = GetAssignableRolesPolicy()
