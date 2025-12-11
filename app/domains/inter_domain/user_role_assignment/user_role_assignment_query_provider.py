# --- 사용자-역할 할당 조회 Provider ---
from sqlalchemy.orm import Session
from typing import List

from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.services.user_role_assignment.schemas.user_role_assignment_query import UserRoleAssignmentRead
from app.domains.services.user_role_assignment.services.user_role_assignment_query_service import user_role_assignment_query_service

class UserRoleAssignmentQueryProvider:
    def get_assignments_for_user(self, db: Session, *, user_id: int) -> List[UserRoleAssignmentRead]:
        """특정 사용자의 모든 역할 할당을 조회하는 안정적인 인터페이스를 제공합니다."""
        return user_role_assignment_query_service.get_assignments_for_user(db=db, user_id=user_id)

user_role_assignment_query_provider = UserRoleAssignmentQueryProvider()
