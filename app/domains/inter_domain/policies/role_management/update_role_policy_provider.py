from sqlalchemy.orm import Session

from app.domains.action_authorization.policies.role_management.update_role_policy import update_role_policy
from app.models.objects.user import User
from app.domains.inter_domain.role_management.schemas.role_command import RoleUpdate

class UpdateRolePolicyProvider:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_id: int,
        role_in: RoleUpdate
    ) -> None:
        return update_role_policy.execute(
            db,
            actor_user=actor_user,
            role_id=role_id,
            role_in=role_in
        )

update_role_policy_provider = UpdateRolePolicyProvider()
