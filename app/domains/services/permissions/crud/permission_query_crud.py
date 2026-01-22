from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.objects.permission import Permission
from app.models.relationships.role_permission import RolePermission
from app.models.relationships.user_organization_role import UserOrganizationRole

class CRUDPermissionQuery(CRUDBase[Permission, None, None]):
    def get_permissions_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> List[Permission]:
        """특정 사용자가 주어진 컨텍스트에서 가지는 모든 고유한 권한을 조회합니다."""
        assignment = db.query(UserOrganizationRole).filter(
            UserOrganizationRole.user_id == user_id,
            UserOrganizationRole.organization_id == organization_id
        ).first()

        if not assignment:
            return []

        permissions = db.query(Permission).join(RolePermission).filter(RolePermission.role_id == assignment.role_id).all()
        
        return permissions

permission_query_crud = CRUDPermissionQuery(Permission)
