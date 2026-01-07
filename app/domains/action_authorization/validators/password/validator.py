import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Union
from pydantic import EmailStr

from app.core.security import verify_password
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.models.objects.user import User

logger = logging.getLogger(__name__)

class PasswordValidator:
    """
    사용자의 비밀번호가 유효한지 확인하고, 실패 시 감사 로그를 기록하는 검증기입니다.
    """
    def validate(self, db: Session, *, email: EmailStr, password: str) -> Tuple[bool, Union[User, str]]:
        """
        제출된 이메일과 비밀번호의 유효성을 검증합니다.

        Returns:
            (True, user_object): 비밀번호가 유효한 경우
            (False, error_message): 사용자가 없거나 비밀번호가 틀린 경우
        """
        user = user_identity_query_provider.get_user_by_email(db, email=email)

        if not user or not verify_password(password, user.password_hash):
            error_msg = f"Incorrect email or password."
            # Log audit event only if the user exists but password was wrong
            if user:
                audit_command_provider.log(
                    db=db,
                    event_type="USER_LOGIN_FAILED",
                    description=f"Failed login attempt for user: {user.username} (email: {email})",
                    actor_user=user,
                    target_user=user,
                    details={"email_attempted": email}
                )
            logger.warning(f"Authorization failed for email '{email}': {error_msg}")
            return False, error_msg

        logger.debug(f"Validation check: Password for user '{user.username}' (email: {email}) is valid.")
        return True, user

password_validator = PasswordValidator()