# --- Query-related Service ---
from sqlalchemy.orm import Session
from typing import List

from app.models.relationships.user_organization_role import UserOrganizationRole
from ..crud.user_role_assignment_query_crud import user_role_assignment_query_crud

class UserRoleAssignmentQueryService:
    def get_assignments_for_user(self, db: Session, *, user_id: int) -> List[UserOrganizationRole]:
        """Gets all role assignments for a specific user."""
        return user_role_assignment_query_crud.get_assignments_by_user(db, user_id=user_id)

user_role_assignment_query_service = UserRoleAssignmentQueryService()
