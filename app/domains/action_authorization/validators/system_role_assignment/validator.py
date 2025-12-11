import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider

logger = logging.getLogger(__name__)

class SystemRoleAssignmentValidator:
    def validate(self, db: Session, *, user_id: int, requested_role_id: int) -> Tuple[bool, Optional[str]]:
        """
        사용자가 이미 요청된 시스템 역할(organization_id가 NULL인 역할)을 가지고 있는지 확인합니다.
        """
        # 요청된 역할이 시스템 역할인지 확인 (organization_id가 NULL인 경우)
        requested_role = role_query_provider.get_role(db, role_id=requested_role_id)
        if not requested_role:
            logger.warning(f"Validation check: Requested role ID {requested_role_id} not found.")
            return False, f"Requested role ID {requested_role_id} not found."

        # 요청된 역할이 시스템 역할이 아니라면 이 검증기의 책임이 아님
        if requested_role.is_system_role == False:
            return True, None # 이 검증기가 처리할 대상이 아니므로 통과
        
        # 사용자가 이미 해당 시스템 역할을 가지고 있는지 확인
        existing_assignment = db.query(UserOrganizationRole).filter(
            UserOrganizationRole.user_id == user_id,
            UserOrganizationRole.role_id == requested_role_id,
            UserOrganizationRole.organization_id.is_(None) # 시스템 역할
        ).first()

        if existing_assignment:
            logger.warning(f"Validation check: User (ID: {user_id}) already has system role ID {requested_role_id}.")
            return False, f"User already has the requested system role."
        
        return True, None

system_role_assignment_validator = SystemRoleAssignmentValidator()
