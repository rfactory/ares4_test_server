from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.objects.user import User
from app.models.objects.role import Role
from app.domains.action_authorization.policies.role_management.get_assignable_roles_policy import get_assignable_roles_policy

class GetAssignableRolesPolicyProvider:
    def execute(self, db: Session, *, actor_user: User, organization_id: Optional[int]) -> List[Role]:
        return get_assignable_roles_policy.execute(db=db, actor_user=actor_user, organization_id=organization_id)

get_assignable_roles_policy_provider = GetAssignableRolesPolicyProvider()