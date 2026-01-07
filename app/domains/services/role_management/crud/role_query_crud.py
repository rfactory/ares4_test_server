from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.objects.role import Role
from ..schemas.role_command import RoleCreate, RoleUpdate

class CRUDRoleQuery(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()

    def get_roles_by_scope(self, db: Session, *, scope: str) -> List[Role]:
        return db.query(self.model).filter(self.model.scope == scope).all()
    
    def get_roles_by_organization_id(self, db: Session, *, organization_id: int) -> List[Role]:
        return db.query(self.model).filter(self.model.organization_id == organization_id).all()

    def get_roles_by_organization_id_and_tier(self, db: Session, *, organization_id: int, tier: int) -> List[Role]:
        """조직 ID와 Tier를 기준으로 역할을 조회합니다."""
        return db.query(self.model).filter(
            self.model.organization_id == organization_id,
            self.model.tier == tier
        ).all()

    def get_multi_by_ids(self, db: Session, *, ids: List[int]) -> List[Role]:
        """ID 목록으로 여러 역할을 조회합니다."""
        return db.query(self.model).filter(self.model.id.in_(ids)).all()

role_query_crud = CRUDRoleQuery(model=Role)
