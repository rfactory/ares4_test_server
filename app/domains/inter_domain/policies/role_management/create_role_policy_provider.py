from sqlalchemy.orm import Session
from typing import Optional

from app.domains.action_authorization.policies.role_management.create_role_policy import create_role_policy
from app.models.objects.user import User
from app.domains.inter_domain.role_management.schemas.role_command import RoleCreate

class CreateRolePolicyProvider:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_in: RoleCreate,
        x_organization_id: Optional[int]
    ) -> None:
        return create_role_policy.execute(
            db, 
            actor_user=actor_user, 
            role_in=role_in,
            x_organization_id=x_organization_id
        )

create_role_policy_provider = CreateRolePolicyProvider()
