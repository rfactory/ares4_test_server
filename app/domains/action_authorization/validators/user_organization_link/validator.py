import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.models.relationships.user_organization_role import UserOrganizationRole
from app.models.objects.user import User
from app.models.objects.organization import Organization

logger = logging.getLogger(__name__)

class UserOrganizationLinkValidator:
    def validate(self, db: Session, *, user: User, organization: Organization, requested_role_id: int) -> Tuple[bool, Optional[str]]:
        """
        사용자가 특정 조직 내에서 요청된 특정 역할을 이미 가지고 있는지 확인합니다.
        """
        existing_link = db.query(UserOrganizationRole).filter(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == organization.id,
            UserOrganizationRole.role_id == requested_role_id
        ).first()

        if existing_link:
            logger.warning(f"Validation check: User '{user.email}' already has role ID '{requested_role_id}' in organization '{organization.name}'.")
            return False, f"User '{user.email}' already has the requested role in the organization."
        
        return True, None

user_organization_link_validator = UserOrganizationLinkValidator()