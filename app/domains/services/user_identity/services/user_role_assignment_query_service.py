from sqlalchemy.orm import Session
from typing import Optional, List

from ..crud.user_role_assignment_query_crud import user_role_assignment_query_crud
from app.models.relationships.user_organization_role import UserOrganizationRole

class UserRoleAssignmentQueryService:
    def get_assignment_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> Optional[UserOrganizationRole]:
        return user_role_assignment_query_crud.get_assignment_for_user_in_context(
            db=db, user_id=user_id, organization_id=organization_id
        )
    
    def get_user_count_for_role(self, db: Session, *, role_id: int) -> int:
        return user_role_assignment_query_crud.get_user_count_for_role(db=db, role_id=role_id)

    def get_assignments_for_user(self, db: Session, *, user_id: int) -> List[UserOrganizationRole]:
        return user_role_assignment_query_crud.get_assignments_for_user(db=db, user_id=user_id)

user_role_assignment_query_service = UserRoleAssignmentQueryService()