from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.role_query_crud import role_query_crud
from app.models.objects.role import Role

class RoleQueryService:
    def get_role(self, db: Session, *, role_id: int) -> Optional[Role]:
        """ID로 역할을 조회합니다."""
        return role_query_crud.get(db, id=role_id)

    def get_role_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        """이름으로 역할을 조회합니다."""
        return role_query_crud.get_by_name(db, name=name)

    def get_all_roles(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Role]:
        """모든 역할을 조회합니다."""
        return role_query_crud.get_multi(db, skip=skip, limit=limit)

role_query_service = RoleQueryService()
