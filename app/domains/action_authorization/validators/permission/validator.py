import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.models.objects.user import User
# core.authorization에 실제 권한 확인 로직이 있다고 가정합니다.
from app.core import authorization

logger = logging.getLogger(__name__)

class PermissionValidator:
    """
    사용자가 특정 권한을 가졌는지 확인하는 범용 검증기입니다.
    시스템 전역 권한과 조직 내 권한을 모두 확인할 수 있습니다.
    """
    def validate(self, db: Session, *, user: User, permission_name: str, organization_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        사용자가 주어진 컨텍스트(organization_id) 내에서 특정 권한(permission_name)을 가졌는지 확인합니다.

        Args:
            db: SQLAlchemy 세션.
            user: 권한을 확인할 사용자 객체.
            permission_name: 확인할 권한의 이름 (예: "audit:read:full").
            organization_id: 권한을 확인할 조직의 ID. None일 경우 시스템 전역 권한을 확인.

        Returns:
            (True, None) if a user has the permission, otherwise (False, error_message).
        """
        has_permission = authorization.check_user_permission(
            db, user=user, permission_name=permission_name, organization_id=organization_id
        )

        if has_permission:
            logger.debug(f"Validation check: User (ID: {user.id}) has permission '{permission_name}' in organization context '{organization_id}'.")
            return True, None
        else:
            error_msg = f"User (ID: {user.id}) does not have permission '{permission_name}' in organization context '{organization_id}'."
            logger.warning(f"Authorization failed: {error_msg}")
            return False, error_msg

permission_validator = PermissionValidator()
