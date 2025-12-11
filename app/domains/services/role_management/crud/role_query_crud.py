from sqlalchemy.orm import Session
from typing import Optional

from app.core.crud_base import CRUDBase
from app.models.objects.role import Role
from ..schemas.role_command import RoleCreate, RoleUpdate

class CRUDRoleQuery(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()

role_query_crud = CRUDRoleQuery(model=Role)
