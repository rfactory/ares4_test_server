import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional
from datetime import datetime, timezone

from app.domains.inter_domain.user_identity.providers import user_identity_providers
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class TwoFactorCodeValidator:
    """
    사용자의 2FA 코드가 유효한지 확인하고, 실패 시 감사 로그를 기록하는 검증기입니다.
    """
    def validate(self, db: Session, *, username: str, code: str) -> Tuple[bool, Optional[str]]:
        """
        제출된 2FA 코드의 유효성을 검증합니다.

        Returns:
            (True, None): 코드가 유효한 경우
            (False, error_message): 사용자가 없거나 코드가 틀리거나 만료된 경우
        """
        user = user_identity_providers.get_user_by_username(db, username=username)

        if not user:
            # PasswordValidator가 먼저 실행되므로 이론적으로는 이 경우에 도달해서는 안 되지만, 안정성을 위해 포함합니다.
            error_msg = f"User '{username}' not found during 2FA validation."
            logger.error(error_msg) # 예기치 않은 상태이므로 error 레벨 사용
            return False, error_msg

        if (
            not user.email_verification_token
            or user.email_verification_token != code
            or not user.email_verification_token_expires_at
            or user.email_verification_token_expires_at < datetime.now(timezone.utc)
        ):
            error_msg = f"Invalid or expired 2FA code for user '{username}'."
            audit_command_provider.log(
                db=db,
                event_type="USER_2FA_FAILED",
                description=f"Failed 2FA attempt for user: {user.username}",
                actor_user=user,
                target_user=user,
                details={"username_attempted": username}
            )
            logger.warning(f"Authorization failed: {error_msg}")
            return False, error_msg

        logger.debug(f"Validation check: 2FA code for user '{username}' is valid.")
        return True, None

two_factor_code_validator = TwoFactorCodeValidator()
