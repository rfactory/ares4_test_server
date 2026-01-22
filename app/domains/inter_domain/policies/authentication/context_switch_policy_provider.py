from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional

from app.domains.action_authorization.policies.authentication.context_switch_policy import context_switch_policy
from app.domains.inter_domain.user_identity.schemas.user_identity_query import UserWithToken

class ContextSwitchPolicyProvider:
    async def execute(
        self,
        db: Session,
        *,
        current_user_jwt: str,
        target_organization_id: int,
        request: Request,
        dpop_jkt: Optional[str] = None
    ) -> UserWithToken:
        return await context_switch_policy.execute(
            db,
            current_user_jwt=current_user_jwt,
            target_organization_id=target_organization_id,
            request=request,
            dpop_jkt=dpop_jkt
        )

context_switch_policy_provider = ContextSwitchPolicyProvider()
