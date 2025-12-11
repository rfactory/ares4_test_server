import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional
from pydantic import EmailStr

from app.models.objects.user import User
from app.domains.inter_domain.user_identity.providers import user_identity_providers

logger = logging.getLogger(__name__)

class UserExistenceValidator:
    def validate(self, db: Session, *, email: EmailStr) -> Tuple[bool, Optional[User]]:
        """
        주어진 이메일로 사용자가 존재하는지 확인합니다.
        사용자가 존재하면 (True, user_object)를, 존재하지 않으면 (False, None)을 반환합니다.
        """
        user = user_identity_providers.get_user_by_email(db, email=email)
        
        if user:
            logger.info(f"Validation check: User with email '{email}' already exists.")
            return True, user
        else:
            logger.info(f"Validation check: User with email '{email}' does not exist.")
            return False, None

user_existence_validator = UserExistenceValidator()
