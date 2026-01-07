from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User
from app.domains.action_authorization.policies.access_requests.create_join_request_policy import create_join_request_policy

class CreateJoinRequestPolicyProvider:
    def execute(
        self,
        db: Session,
        *,
        requester_user: User,
        org_identifier: str,
        reason: Optional[str]
    ):
        return create_join_request_policy.execute(
            db,
            requester_user=requester_user,
            org_identifier=org_identifier,
            reason=reason
        )

create_join_request_policy_provider = CreateJoinRequestPolicyProvider()