from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.domains.action_authorization.policies.access_requests.reject_request_policy import reject_request_policy

class RejectRequestPolicyProvider:
    def execute(self, db: Session, *, request_id: int, admin_user: User):
        return reject_request_policy.execute(
            db=db,
            request_id=request_id,
            admin_user=admin_user
        )

reject_request_policy_provider = RejectRequestPolicyProvider()
