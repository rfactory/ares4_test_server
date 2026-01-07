from typing import Tuple, Optional
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.models.objects.user import User
from app.domains.action_authorization.validators.user_existence.validator import user_existence_validator

class UserExistenceValidatorProvider:
    """
    `user_existence` validator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(self, db: Session, *, email: EmailStr) -> Tuple[bool, Optional[User]]:
        """
        주어진 이메일로 사용자가 존재하는지 검증합니다.
        """
        return user_existence_validator.validate(db, email=email)

user_existence_validator_provider = UserExistenceValidatorProvider()
