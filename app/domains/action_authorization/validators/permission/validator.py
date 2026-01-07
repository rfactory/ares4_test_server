import logging
from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User
from app.core import authorization
from app.core.exceptions import ForbiddenError # ForbiddenError 임포트

logger = logging.getLogger(__name__)

class PermissionValidator:
    """
    사용자가 특정 권한을 가졌는지 확인하는 범용 검증기입니다.
    시스템 전역 권한과 조직 내 권한을 모두 확인할 수 있습니다.
    실패 시 ForbiddenError를 발생시킵니다.
    """
    def validate(self, db: Session, *, user: User, permission_name: str, organization_id: Optional[int] = None) -> None:
        """
        사용자가 주어진 컨텍스트(organization_id) 내에서 특정 권한(permission_name)을 가졌는지 확인합니다.
        권한이 없으면 ForbiddenError를 발생시킵니다.

        Args:
            db: SQLAlchemy 세션.
            user: 권한을 확인할 사용자 객체.
            permission_name: 확인할 권한의 이름 (예: "audit:read:full").
            organization_id: 권한을 확인할 조직의 ID. None일 경우 시스템 전역 권한을 확인.
        """
        has_permission = authorization.authorization_service.check_user_permission(
            db, user=user, permission_name=permission_name, organization_id=organization_id
        )

        if not has_permission:
            error_msg = f"User (ID: {user.id}) does not have permission '{permission_name}' in organization context '{organization_id}'."
            logger.warning(f"Authorization failed: {error_msg}")
            raise ForbiddenError(error_msg)
        
        logger.debug(f"Validation check: User (ID: {user.id}) has permission '{permission_name}' in organization context '{organization_id}'.")

permission_validator = PermissionValidator()
