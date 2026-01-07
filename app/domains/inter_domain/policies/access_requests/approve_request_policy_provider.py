from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.domains.action_authorization.policies.access_requests.approve_request_policy import approve_request_policy

class ApproveRequestPolicyProvider:
    def execute(self, db: Session, *, request_id: int, admin_user: User):
        return approve_request_policy.execute(
            db=db,
            request_id=request_id,
            admin_user=admin_user
        )

approve_request_policy_provider = ApproveRequestPolicyProvider()
