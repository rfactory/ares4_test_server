from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.action_authorization.policies.access_requests.accept_invitation_policy import accept_invitation_policy

class AcceptInvitationPolicyProvider:
    async def execute(self, db: Session, *, accepting_user: User, verification_code: str):
        return await accept_invitation_policy.execute(
            db=db, 
            accepting_user=accepting_user, 
            verification_code=verification_code
        )

accept_invitation_policy_provider = AcceptInvitationPolicyProvider()
