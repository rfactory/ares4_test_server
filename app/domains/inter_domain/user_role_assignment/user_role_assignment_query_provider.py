# --- 사용자-역할 할당 조회 Provider ---
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.services.user_role_assignment.schemas.user_role_assignment_query import UserRoleAssignmentRead
from app.domains.services.user_identity.services.user_role_assignment_query_service import user_role_assignment_query_service

class UserRoleAssignmentQueryProvider:
    def get_assignments_for_user(self, db: Session, *, user_id: int) -> List[UserRoleAssignmentRead]:
        """특정 사용자의 모든 역할 할당을 조회하는 안정적인 인터페이스를 제공합니다."""
        return user_role_assignment_query_service.get_assignments_for_user(db=db, user_id=user_id)

    def get_user_count_for_role(self, db: Session, *, role_id: int) -> int:
        """특정 역할에 할당된 사용자 수를 조회하는 안정적인 인터페이스를 제공합니다."""
        return user_role_assignment_query_service.get_user_count_for_role(db=db, role_id=role_id)

    def get_assignment_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> Optional[UserOrganizationRole]:
        """특정 컨텍스트에서 사용자의 역할 할당 정보를 조회합니다."""
        return user_role_assignment_query_service.get_assignment_for_user_in_context(
            db=db, user_id=user_id, organization_id=organization_id
        )

user_role_assignment_query_provider = UserRoleAssignmentQueryProvider()
