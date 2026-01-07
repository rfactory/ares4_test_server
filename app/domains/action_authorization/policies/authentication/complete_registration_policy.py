from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, NotFoundError

# Schemas
from ....inter_domain.token.schemas.token_command import Token

# Providers
from ....inter_domain.registration_cache.registration_cache_query_provider import registration_cache_query_provider
from ....inter_domain.registration_cache.registration_cache_command_provider import registration_cache_command_provider
from ....inter_domain.user_identity.user_identity_command_provider import user_identity_command_provider
from ....inter_domain.token.token_command_provider import token_command_provider

class CompleteRegistrationPolicy:
    def execute(self, db: Session, *, verification_code: str, email: str) -> dict:
        """
        제출된 인증 코드를 검증하고, 최종적으로 사용자 생성을 완료한 후 토큰을 발급합니다.
        """
        # 1. Redis에서 임시 데이터 조회
        temp_data = registration_cache_query_provider.get_registration_data(code=verification_code)
        if not temp_data:
            raise NotFoundError(resource_name="Verification Code", resource_id=verification_code)

        # 2. 이메일 일치 여부 확인
        if temp_data.email != email:
            raise ValidationError("Email does not match the verification code.")

        # 3. 최종 사용자 생성 (is_active=True로)
        new_user = user_identity_command_provider.create_user_with_prehashed_password(
            db, user_data=temp_data.model_dump(), is_active=True
        )

        # 4. Redis 키 삭제
        registration_cache_command_provider.delete_registration_data(code=verification_code)

        # 5. 토큰 발급 (즉시 로그인)
        token = token_command_provider.issue_token(db, user=new_user)

        return {"user": new_user.as_dict(), "token": token.model_dump()}

complete_registration_policy = CompleteRegistrationPolicy()
