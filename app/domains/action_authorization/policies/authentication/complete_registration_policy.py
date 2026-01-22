from sqlalchemy.orm import Session
from fastapi import Request # Request 임포트

from app.core.exceptions import ValidationError, NotFoundError
from app.core.security import verify_dpop_proof # DPoP 검증 함수 임포트

# Providers
from app.domains.inter_domain.registration_cache.registration_cache_query_provider import registration_cache_query_provider
from app.domains.inter_domain.registration_cache.registration_cache_command_provider import registration_cache_command_provider
from app.domains.inter_domain.user_identity.user_identity_command_provider import user_identity_command_provider
from app.domains.inter_domain.token_management.token_management_command_provider import token_management_command_provider

class CompleteRegistrationPolicy:
    async def execute(self, db: Session, *, verification_code: str, email: str, request: Request) -> dict:
        """
        제출된 인증 코드를 검증하고, 최종적으로 사용자 생성을 완료한 후 DPoP 바인딩된 토큰을 발급합니다.
        """
        # 1. Redis에서 임시 데이터 조회
        temp_data = registration_cache_query_provider.get_registration_data(code=verification_code)
        if not temp_data:
            raise NotFoundError(resource_name="Verification Code", resource_id=verification_code)

        # 2. 이메일 일치 여부 확인
        if temp_data.email != email:
            raise ValidationError("Email does not match the verification code.")

        # 3. DPoP 헤더 검증 및 jkt 추출
        dpop_jkt = await verify_dpop_proof(request, access_token=None)

        # 4. 최종 사용자 생성 (is_active=True로)
        new_user = user_identity_command_provider.create_user_with_prehashed_password(
            db, user_data=temp_data.model_dump(), is_active=True
        )

        # 5. Redis 키 삭제
        registration_cache_command_provider.delete_registration_data(code=verification_code)

        # 6. 토큰 발급 (즉시 로그인, DPoP jkt 포함)
        token_pair = token_management_command_provider.issue_token_pair(db, user=new_user, dpop_jkt=dpop_jkt)

        return {"user": new_user.as_dict(), "token": token_pair}

complete_registration_policy = CompleteRegistrationPolicy()
