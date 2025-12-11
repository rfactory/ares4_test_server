import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.core.security import verify_password
from app.domains.inter_domain.user_identity.providers import user_identity_providers
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class PasswordValidator:
    """
    사용자의 비밀번호가 유효한지 확인하고, 실패 시 감사 로그를 기록하는 검증기입니다.
    """
    def validate(self, db: Session, *, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        제출된 사용자 이름과 비밀번호의 유효성을 검증합니다.

        Returns:
            (True, None): 비밀번호가 유효한 경우
            (False, error_message): 사용자가 없거나 비밀번호가 틀린 경우
        """
        user = user_identity_providers.get_user_by_username(db, username=username)

        if not user or not verify_password(password, user.password_hash):
            error_msg = f"Incorrect username or password."
            # Log audit event only if the user exists but password was wrong
            if user:
                audit_command_provider.log(
                    db=db,
                    event_type="USER_LOGIN_FAILED",
                    description=f"Failed login attempt for user: {user.username}",
                    actor_user=user,
                    target_user=user,
                    details={"username_attempted": username}
                )
            logger.warning(f"Authorization failed for user '{username}': {error_msg}")
            return False, error_msg

        logger.debug(f"Validation check: Password for user '{username}' is valid.")
        return True, None

password_validator = PasswordValidator()