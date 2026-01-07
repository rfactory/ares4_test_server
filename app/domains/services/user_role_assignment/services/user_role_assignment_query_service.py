# --- Query-related Service ---
from sqlalchemy.orm import Session
from typing import List

from app.models.relationships.user_organization_role import UserOrganizationRole
from ..crud.user_role_assignment_query_crud import user_role_assignment_query_crud

class UserRoleAssignmentQueryService:
    def get_assignments_for_user(self, db: Session, *, user_id: int) -> List[UserOrganizationRole]:
        """Gets all role assignments for a specific user."""
        return user_role_assignment_query_crud.get_assignments_by_user(db, user_id=user_id)

    def get_user_count_for_role(self, db: Session, *, role_id: int) -> int:
        """Gets the number of users assigned to a specific role."""
        return user_role_assignment_query_crud.get_count_by_role_id(db, role_id=role_id)

user_role_assignment_query_service = UserRoleAssignmentQueryService()
