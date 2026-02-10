from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.objects.permission import Permission
from app.models.relationships.role_permission import RolePermission
from app.models.relationships.user_organization_role import UserOrganizationRole

class CRUDPermissionQuery(CRUDBase[Permission, None, None]):
    def get_permissions_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> List[Permission]:
        # 1. 먼저 사용자가 가진 모든 '역할 할당'을 가져옵니다.
        query = db.query(UserOrganizationRole).filter(UserOrganizationRole.user_id == user_id)

        # 2. 만약 조직 ID가 지정되었다면 해당 조직 것만 가져오고,
        # 지정되지 않았다면(System/Personal) 모든 권한을 다 긁어오거나 시스템용만 필터링하도록 선택할 수 있습니다.
        if organization_id is not None:
            query = query.filter(UserOrganizationRole.organization_id == organization_id)
        # else: 
        #   여기서 아무 필터도 걸지 않으면 유저가 가진 '모든 조직의 모든 역할'을 합산하게 됩니다.

        assignments = query.all()
        if not assignments:
            return []

        # 3. 찾은 모든 역할들에 연결된 권한 리스트 추출
        role_ids = [a.role_id for a in assignments]
        return db.query(Permission).join(RolePermission).filter(RolePermission.role_id.in_(role_ids)).distinct().all()
permission_query_crud = CRUDPermissionQuery(Permission)
