from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.models.objects.role import Role
from app.models.objects.user import User
from ..crud.role_command_crud import role_command_crud
from ..crud.role_query_crud import role_query_crud
from ..schemas.role_command import RoleCreate, RoleUpdate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class RoleCommandService:
    def create_role(self, db: Session, *, role_in: RoleCreate, actor_user: User) -> Role:
        """새로운 역할을 생성합니다."""
        existing_role = role_query_crud.get_by_name(db, name=role_in.name)
        if existing_role:
            raise DuplicateEntryError("Role", "name", role_in.name)

        new_role = role_command_crud.create(db, obj_in=role_in)
        db.flush()

        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="Role",
            resource_id=new_role.id,
            new_value=new_role.as_dict()
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

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="Role",
            resource_id=updated_role.id,
            old_value=old_value,
            new_value=updated_role.as_dict()
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

        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="Role",
            resource_id=role_id,
            deleted_value=deleted_value
        )
        return deleted_role

role_command_service = RoleCommandService()
