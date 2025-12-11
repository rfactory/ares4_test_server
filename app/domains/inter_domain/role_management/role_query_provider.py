from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.role_management.services.role_query_service import role_query_service
from app.models.objects.role import Role

class RoleQueryProvider:
    def get_role(self, db: Session, *, role_id: int) -> Optional[Role]:
        return role_query_service.get_role(db, role_id=role_id)

    def get_role_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        return role_query_service.get_role_by_name(db, name=name)

    def get_all_roles(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Role]:
        return role_query_service.get_all_roles(db, skip=skip, limit=limit)

role_query_provider = RoleQueryProvider()
