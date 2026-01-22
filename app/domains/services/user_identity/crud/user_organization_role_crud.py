from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.services.user_identity.schemas.user_identity_command import UserRoleAssignmentCreate, UserRoleAssignmentUpdate

class CRUDUserOrganizationRole(CRUDBase[UserOrganizationRole, UserRoleAssignmentCreate, UserRoleAssignmentUpdate]):
    def delete_by_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> int:
        """특정 컨텍스트에 있는 사용자의 모든 역할 할당을 삭제합니다."""
        num_deleted = db.query(self.model).filter(
            self.model.user_id == user_id, 
            self.model.organization_id == organization_id
        ).delete(synchronize_session=False)
        return num_deleted

user_organization_role_crud = CRUDUserOrganizationRole(model=UserOrganizationRole)