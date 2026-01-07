from sqlalchemy.orm import Session
from typing import Tuple, Optional, Union
from pydantic import EmailStr

from app.models.objects.user import User
from app.domains.action_authorization.validators.password.validator import password_validator

class PasswordValidatorProvider:
    """
    로그인 시 비밀번호 일치 여부를 검증하는 validator를 외부 도메인에 노출하는 제공자입니다.
    """
    def validate_password(self, db: Session, *, email: EmailStr, password: str) -> Tuple[bool, Union[User, str]]:
        """
        제출된 이메일과 비밀번호의 유효성을 검증합니다.
        """
        return password_validator.validate(db, email=email, password=password)

password_validator_provider = PasswordValidatorProvider()
