from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.action_authorization.policies.access_requests.create_invitation_policy import create_invitation_policy
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestInvite

class CreateInvitationPolicyProvider:
    def execute(self, db: Session, *, actor_user: User, invitation_in: AccessRequestInvite):
        return create_invitation_policy.execute(
            db=db, 
            actor_user=actor_user, 
            invitation_in=invitation_in
        )

create_invitation_policy_provider = CreateInvitationPolicyProvider()
