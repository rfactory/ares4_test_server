import logging
from sqlalchemy.orm import Session
from fastapi import Request

# Providers
from app.domains.inter_domain.token_management.token_management_query_provider import token_management_query_provider
from app.domains.inter_domain.validators.refresh_token.refresh_token_validator_provider import refresh_token_validator_provider
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.token_management.token_management_command_provider import token_management_command_provider
from app.domains.inter_domain.validators.object_existence.object_existence_validator_provider import object_existence_validator_provider
from app.core.security import verify_dpop_proof
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class RefreshTokenPolicy:
    async def execute(self, db: Session, *, old_refresh_token: str, request: Request) -> dict:
        """
        [오케스트레이터] Refresh Token 순환의 전체 과정을 지휘합니다.
        1. 데이터 조회 (Query)
        2. 데이터 검증 (Validate)
        3. 데이터 조작 (Command)
        """
        # 1. 데이터 조회: Refresh Token 객체 및 payload를 가져옵니다.
        token_obj = token_management_query_provider.get_refresh_token_obj(db, token=old_refresh_token)
        token_payload = token_management_query_provider.get_token_payload(token=old_refresh_token)
        user = user_identity_query_provider.get_user(db, user_id=token_payload.id)

        # 2. 데이터 검증: 토큰 객체와 사용자 객체의 유효성을 검사합니다.
        refresh_token_validator_provider.validate(token_obj=token_obj)
        object_existence_validator_provider.validate(
            obj=user, 
            obj_name="User", 
            identifier=str(token_payload.id), 
            should_exist=True
        )
        
        # 3. DPoP 헤더 검증 및 jkt 추출
        dpop_jkt = await verify_dpop_proof(request, access_token=None) # DPoP 헤더 검증 및 jkt 추출

        # 4. 데이터 조작 (토큰 순환)
        new_token_pair = token_management_command_provider.rotate_token(
            db, 
            refresh_token_obj=token_obj, 
            user=user,
            dpop_jkt=dpop_jkt # dpop_jkt 전달
        )
        
        # 5. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="TOKEN_REFRESHED",
            description=f"Token refreshed for User ID: {user.id}",
            actor_user=user,
            details={"user_id": user.id, "token_id": token_obj.id}
        )
        
        # 6. 트랜잭션 커밋
        db.commit()
        
        return new_token_pair

refresh_token_policy = RefreshTokenPolicy()