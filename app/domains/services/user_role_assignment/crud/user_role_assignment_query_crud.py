# --- Query-related CRUD ---
from sqlalchemy.orm import Session
from typing import List

from app.models.relationships.user_organization_role import UserOrganizationRole

class CRUDUserRoleAssignmentQuery:
    def get_assignments_by_user(self, db: Session, *, user_id: int) -> List[UserOrganizationRole]:
        """Get all role assignments for a specific user."""
        return db.query(UserOrganizationRole).filter(UserOrganizationRole.user_id == user_id).all()

user_role_assignment_query_crud = CRUDUserRoleAssignmentQuery()
