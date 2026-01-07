from sqlalchemy.orm import Session
from typing import List # List 추가

from app.domains.services.role_management.services.role_command_service import role_command_service
from app.domains.services.role_management.schemas.role_command import RoleCreate, RoleUpdate, PermissionAssignment # 스키마 추가
from app.models.objects.role import Role
from app.models.objects.user import User

class RoleCommandProvider:
    def create_role(self, db: Session, *, role_in: RoleCreate, actor_user: User) -> Role:
        return role_command_service.create_role(db, role_in=role_in, actor_user=actor_user)

    def update_role(self, db: Session, *, role_id: int, role_in: RoleUpdate, actor_user: User) -> Role:
        return role_command_service.update_role(db, role_id=role_id, role_in=role_in, actor_user=actor_user)

    def delete_role(self, db: Session, *, role_id: int, actor_user: User) -> Role:
        return role_command_service.delete_role(db, role_id=role_id, actor_user=actor_user)

    def update_permissions_for_role(self, db: Session, *, role_id: int, permissions_in: List[PermissionAssignment], actor_user: User) -> None:
        return role_command_service.update_permissions_for_role(
            db, role_id=role_id, permissions_in=permissions_in, actor_user=actor_user
        )

role_command_provider = RoleCommandProvider()
