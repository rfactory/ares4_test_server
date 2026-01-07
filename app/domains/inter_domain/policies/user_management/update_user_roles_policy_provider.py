from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.objects.user import User
from app.models.objects.role import Role
from app.domains.action_authorization.policies.user_management.update_user_roles_policy import update_user_roles_policy

class UpdateUserRolesPolicyProvider:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_user: User, 
        roles_to_assign: Optional[List[Role]] = None,
        roles_to_revoke: Optional[List[Role]] = None
    ) -> None:
        return update_user_roles_policy.execute(
            db,
            actor_user=actor_user,
            target_user=target_user,
            roles_to_assign=roles_to_assign,
            roles_to_revoke=roles_to_revoke
        )

update_user_roles_policy_provider = UpdateUserRolesPolicyProvider()
