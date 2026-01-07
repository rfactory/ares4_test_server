from typing import List, Optional
from sqlalchemy.orm import Session

from app.domains.action_authorization.policies.role_management.update_role_permissions_policy import update_role_permissions_policy
from app.models.objects.user import User
from app.domains.inter_domain.role_management.schemas.role_command import PermissionAssignment

class UpdateRolePermissionsPolicyProvider:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_role_id: int, 
        permissions_in: List[PermissionAssignment],
        x_organization_id: Optional[int]
    ) -> None:
        return update_role_permissions_policy.execute(
            db, 
            actor_user=actor_user, 
            target_role_id=target_role_id, 
            permissions_in=permissions_in,
            x_organization_id=x_organization_id
        )

update_role_permissions_policy_provider = UpdateRolePermissionsPolicyProvider()
