from sqlalchemy.orm import Session

from app.domains.services.role_management.services.role_command_service import role_command_service
from app.domains.services.role_management.schemas.role_command import RoleCreate, RoleUpdate
from app.models.objects.role import Role
from app.models.objects.user import User

class RoleCommandProvider:
    def create_role(self, db: Session, *, role_in: RoleCreate, actor_user: User) -> Role:
        return role_command_service.create_role(db, role_in=role_in, actor_user=actor_user)

    def update_role(self, db: Session, *, role_id: int, role_in: RoleUpdate, actor_user: User) -> Role:
        return role_command_service.update_role(db, role_id=role_id, role_in=role_in, actor_user=actor_user)

    def delete_role(self, db: Session, *, role_id: int, actor_user: User) -> Role:
        return role_command_service.delete_role(db, role_id=role_id, actor_user=actor_user)

role_command_provider = RoleCommandProvider()
