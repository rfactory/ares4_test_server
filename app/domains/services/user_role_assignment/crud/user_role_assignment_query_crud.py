# --- Query-related CRUD ---
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.models.relationships.user_organization_role import UserOrganizationRole

class CRUDUserRoleAssignmentQuery:
    def get_assignments_by_user(self, db: Session, *, user_id: int) -> List[UserOrganizationRole]:
        """Get all role assignments for a specific user."""
        return db.query(UserOrganizationRole).filter(UserOrganizationRole.user_id == user_id).all()

    def get_count_by_role_id(self, db: Session, *, role_id: int) -> int:
        """Get the number of users assigned to a specific role."""
        return db.query(func.count(UserOrganizationRole.user_id)).filter(UserOrganizationRole.role_id == role_id).scalar() or 0

user_role_assignment_query_crud = CRUDUserRoleAssignmentQuery()
