from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.domains.action_authorization.policies.user_management.switch_context_policy import switch_context_policy

class SwitchContextPolicyProvider:
    def switch_to_organization_context(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_organization_id: int
    ) -> Organization:
        return switch_context_policy.switch_to_organization_context(
            db,
            actor_user=actor_user,
            target_organization_id=target_organization_id
        )

switch_context_policy_provider = SwitchContextPolicyProvider()
