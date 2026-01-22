import logging
from typing import Optional

from app.core.security import verify_password
from app.models.objects.user import User
from app.core.exceptions import AuthenticationError # 예외 임포트

logger = logging.getLogger(__name__)

class PasswordValidator:
    """
    사용자의 비밀번호가 유효한지 확인하는 순수 검증기입니다.
    """
    def validate(self, *, password: str, user: Optional[User]):
        """
        사용자 객체와 제출된 비밀번호의 유효성을 검증합니다.
        사용자가 없거나 비밀번호가 틀리면 AuthenticationError를 발생시킵니다.
        """
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError(f"Incorrect email or password.")

        logger.debug(f"Validation check: Password for user '{user.username}' is valid.")

password_validator = PasswordValidator()