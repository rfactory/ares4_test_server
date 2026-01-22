from sqlalchemy.orm import Session
from fastapi import Request # Request 임포트
from app.domains.action_authorization.policies.authentication.refresh_token_policy import refresh_token_policy

class RefreshTokenPolicyProvider:
    async def execute(self, db: Session, *, old_refresh_token: str, request: Request) -> dict:
        """RefreshTokenPolicy를 호출하여 토큰 순환을 실행합니다."""
        return await refresh_token_policy.execute(db=db, old_refresh_token=old_refresh_token, request=request)

refresh_token_policy_provider = RefreshTokenPolicyProvider()