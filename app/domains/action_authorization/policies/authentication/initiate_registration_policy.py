import redis
import json
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEntryError, ValidationError
from app.core.config import settings
from app.core.utils import generate_random_code

# Schemas
from app.domains.inter_domain.user_identity.schemas.user_identity_command import UserCreate
from app.domains.inter_domain.send_email.schemas.send_email_command import EmailSchema
from app.domains.inter_domain.registration_cache.schemas.registration_cache_command import CacheRegistrationData

# Query Providers
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider

# Validator Providers
from app.domains.inter_domain.validators.object_existence.object_existence_validator_provider import object_existence_validator_provider
from app.domains.inter_domain.validators.password_strength.password_strength_validator_provider import password_strength_validator_provider

# Command Providers
from app.domains.inter_domain.user_identity.user_identity_command_provider import user_identity_command_provider
from app.domains.inter_domain.send_email.send_email_command_provider import send_email_command_provider
from app.domains.inter_domain.registration_cache.registration_cache_command_provider import registration_cache_command_provider

from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

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
        # 1.1. 이메일 중복 검사 (Query Provider 호출 -> 순수 Validator 호출)
        existing_user = user_identity_query_provider.get_user_by_email(db, email=user_in.email)
        object_existence_validator_provider.validate(
            obj=existing_user, 
            obj_name="User", 
            identifier=user_in.email, 
            should_exist=False
        )

        # 1.2. 비밀번호 강도 검사 (순수 Validator 호출)
        password_strength_validator_provider.validate(user_in.password)

        # 2. 코드 생성 및 데이터 준비
        verification_code = generate_random_code()
        hashed_password = user_identity_command_provider.get_password_hash(password=user_in.password) # Provider 호출

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
        
        # 5. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="REGISTRATION_STARTED",
            description=f"Registration initiated for email: {user_in.email}",
            actor_user=None, # 아직 가입 전이므로 행위자 없음
            details={"email": user_in.email}
        )
        
        # 6. 트랜잭션 커밋
        db.commit()
        
        return {"message": "Verification code sent to email."}

initiate_registration_policy = InitiateRegistrationPolicy()