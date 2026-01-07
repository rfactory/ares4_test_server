import redis
import json
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEntryError, ValidationError
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.utils import generate_random_code

# Schemas
from ....inter_domain.user_identity.schemas.user_identity_command import UserCreate
from ....inter_domain.send_email.schemas.send_email_command import EmailSchema
from ....inter_domain.registration_cache.schemas.registration_cache_command import CacheRegistrationData

# Validator Providers
from ....inter_domain.validators.user_existence.user_existence_validator_provider import user_existence_validator_provider
from ....inter_domain.validators.password_strength.password_strength_validator_provider import password_strength_validator_provider

# Service Providers
from ....inter_domain.send_email.send_email_command_provider import send_email_command_provider
from ....inter_domain.registration_cache.registration_cache_command_provider import registration_cache_command_provider

class InitiateRegistrationPolicy:
    async def execute(self, db: Session, *, user_in: UserCreate):
        """
        새로운 사용자 가입 절차를 시작합니다.
        1. 데이터 유효성 검사 (이메일 중복, 비밀번호 강도)
        2. 인증 코드 생성
        3. Redis에 임시 가입 정보 저장
        4. 이메일 발송
        """
        # 1. 유효성 검사
        is_exist, _ = user_existence_validator_provider.validate(db, email=user_in.email)
        if is_exist:
            raise DuplicateEntryError("User", "email", user_in.email)

        is_strong, reason = password_strength_validator_provider.validate_strength(user_in.password)
        if not is_strong:
            raise ValidationError(reason)

        # 2. 코드 생성 및 데이터 준비
        verification_code = generate_random_code()
        hashed_password = get_password_hash(user_in.password)

        # Create a Pydantic model instance instead of a dict
        cache_data = CacheRegistrationData(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password
        )

        # 3. Redis에 임시 저장 (Service 호출)
        registration_cache_command_provider.cache_registration_data(
            data=cache_data, code=verification_code, ttl_seconds=600
        )

        # 4. 이메일 발송 (Mock)
        email_data = EmailSchema(
            to=user_in.email,
            subject="Verify your email address for Ares4",
            template_name="email_verification.html",
            context={"verification_code": verification_code}
        )
        await send_email_command_provider.send_email(email_data=email_data)

        return {"message": "Verification code sent to email."}

initiate_registration_policy = InitiateRegistrationPolicy()