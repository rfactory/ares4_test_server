from typing import List
from sqlalchemy.orm import Session

from app.core.crud_base import CRUDBase
from app.models.relationships.role_permission import RolePermission

class CRUDRolePermissionQuery(CRUDBase[RolePermission, None, None]):
    def get_by_role_id(self, db: Session, *, role_id: int) -> List[RolePermission]:
        """특정 역할 ID에 할당된 모든 권한 관계를 조회합니다."""
        return db.query(self.model).filter(self.model.role_id == role_id).all()

role_permission_query_crud = CRUDRolePermissionQuery(RolePermission)
