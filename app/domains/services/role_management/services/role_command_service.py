from sqlalchemy.orm import Session
from typing import List

from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.models.objects.role import Role
from app.models.objects.user import User
from ..crud.role_command_crud import role_command_crud
from ..crud.role_query_crud import role_query_crud
from ..crud.role_permission_command_crud import role_permission_command_crud
from ..schemas.role_command import RoleCreate, RoleUpdate, RolePermissionUpdateRequest, PermissionAssignment
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class RoleCommandService:
    def create_role(self, db: Session, *, role_in: RoleCreate, actor_user: User) -> Role:
        """새로운 역할을 생성합니다."""
        existing_role = role_query_crud.get_by_name(db, name=role_in.name)
        if existing_role:
            raise DuplicateEntryError("Role", "name", role_in.name)

        new_role = role_command_crud.create(db, obj_in=role_in)
        db.flush()

        audit_command_provider.log(
            db=db, event_type="ROLE_CREATED", actor_user=actor_user,
            description=f"Role '{new_role.name}' created.", details={"new_value": new_role.as_dict()}
        )
        return new_role

    def update_role(self, db: Session, *, role_id: int, role_in: RoleUpdate, actor_user: User) -> Role:
        """역할 정보를 업데이트합니다."""
        db_role = role_query_crud.get(db, id=role_id)
        if not db_role:
            raise NotFoundError("Role", str(role_id))

        if role_in.name != db_role.name:
            existing_role = role_query_crud.get_by_name(db, name=role_in.name)
            if existing_role:
                raise DuplicateEntryError("Role", "name", role_in.name)

        old_value = db_role.as_dict()
        updated_role = role_command_crud.update(db, db_obj=db_role, obj_in=role_in)
        db.flush()

        audit_command_provider.log(
            db=db, event_type="ROLE_UPDATED", actor_user=actor_user,
            description=f"Role '{updated_role.name}' updated.", details={"old_value": old_value, "new_value": updated_role.as_dict()}
        )
        return updated_role

    def delete_role(self, db: Session, *, role_id: int, actor_user: User) -> Role:
        """역할을 삭제합니다."""
        db_role = role_query_crud.get(db, id=role_id)
        if not db_role:
            raise NotFoundError("Role", str(role_id))

        deleted_value = db_role.as_dict()
        deleted_role = role_command_crud.remove(db, id=role_id)
        db.flush()

        audit_command_provider.log(
            db=db, event_type="ROLE_DELETED", actor_user=actor_user,
            description=f"Role '{deleted_value['name']}' deleted.", details={"deleted_value": deleted_value}
        )
        return deleted_role

    def update_permissions_for_role(self, db: Session, *, role_id: int, permissions_in: List[PermissionAssignment], actor_user: User):
        """역할에 할당된 권한 목록 전체를 업데이트합니다."""
        # 1. 기존 권한 할당을 모두 삭제
        role_permission_command_crud.remove_by_role_id(db, role_id=role_id)

        # 2. 새로운 권한 할당 목록을 대량으로 추가
        if permissions_in:
            role_permission_command_crud.bulk_create(db, role_id=role_id, permissions=permissions_in)
        
        # 감사 로그 (단순화를 위해, 상세 변경 내역은 생략)
        audit_command_provider.log(
            db=db, event_type="ROLE_PERMISSIONS_UPDATED", actor_user=actor_user,
            description=f"Permissions for role ID {role_id} updated.",
            details={"role_id": role_id, "new_permission_count": len(permissions_in)}
        )

role_command_service = RoleCommandService()

