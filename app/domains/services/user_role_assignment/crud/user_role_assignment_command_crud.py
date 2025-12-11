# --- Command-related CRUD ---
from sqlalchemy.orm import Session
from typing import Optional

from app.core.crud_base import CRUDBase
from app.models.relationships.user_organization_role import UserOrganizationRole
from ..schemas.user_role_assignment_command import UserRoleAssignmentCreate

class CRUDUserRoleAssignmentCommand(CRUDBase[UserOrganizationRole, UserRoleAssignmentCreate, dict]): # Using dict for update as it's not defined
    def get_by_user_role_org(
        self, db: Session, *, user_id: int, role_id: int, organization_id: Optional[int]
    ) -> Optional[UserOrganizationRole]:
        """Check for an existing role assignment."""
        return (
            db.query(UserOrganizationRole)
            .filter(
                UserOrganizationRole.user_id == user_id,
                UserOrganizationRole.role_id == role_id,
                UserOrganizationRole.organization_id == organization_id,
            )
            .first()
        )

user_role_assignment_crud_command = CRUDUserRoleAssignmentCommand(UserOrganizationRole)
