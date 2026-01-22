from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.crud_base import CRUDBase
from app.models.relationships.user_organization_role import UserOrganizationRole

class CRUDUserRoleAssignmentQuery(CRUDBase[UserOrganizationRole, None, None]):
    def get_assignment_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> Optional[UserOrganizationRole]:
        return db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.organization_id == organization_id
        ).first()

    def get_user_count_for_role(self, db: Session, *, role_id: int) -> int:
        return db.query(self.model).filter(self.model.role_id == role_id).count()

    def get_assignments_for_user(self, db: Session, *, user_id: int) -> List[UserOrganizationRole]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

user_role_assignment_query_crud = CRUDUserRoleAssignmentQuery(model=UserOrganizationRole)