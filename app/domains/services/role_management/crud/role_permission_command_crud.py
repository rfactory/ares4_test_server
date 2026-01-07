from typing import List
from sqlalchemy.orm import Session

from app.core.crud_base import CRUDBase
from app.models.relationships.role_permission import RolePermission
from ..schemas.role_command import PermissionAssignment

class CRUDRolePermissionCommand(CRUDBase[RolePermission, None, None]):
    def remove_by_role_id(self, db: Session, *, role_id: int) -> int:
        """특정 역할 ID에 연결된 모든 권한 할당을 삭제합니다."""
        num_deleted = db.query(self.model).filter(self.model.role_id == role_id).delete()
        return num_deleted

    def bulk_create(self, db: Session, *, role_id: int, permissions: List[PermissionAssignment]):
        """새로운 권한 할당 목록을 대량으로 생성합니다."""
        new_assignments = [
            self.model(
                role_id=role_id, 
                permission_id=p.permission_id, 
                allowed_columns=p.allowed_columns, 
                filter_condition=p.filter_condition
            ) for p in permissions
        ]
        db.bulk_save_objects(new_assignments)

role_permission_command_crud = CRUDRolePermissionCommand(RolePermission)
