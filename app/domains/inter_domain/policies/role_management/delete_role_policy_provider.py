from sqlalchemy.orm import Session

from app.domains.action_authorization.policies.role_management.delete_role_policy import delete_role_policy
from app.models.objects.user import User

class DeleteRolePolicyProvider:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_id: int
    ) -> None:
        return delete_role_policy.execute(
            db, 
            actor_user=actor_user, 
            role_id=role_id
        )

delete_role_policy_provider = DeleteRolePolicyProvider()
