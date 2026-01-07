from typing import List
from sqlalchemy.orm import Session

from app.models.objects.permission import Permission
from ..crud.permission_query_crud import permission_query_crud

class PermissionQueryService:
    def get_all_permissions(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Permission]:
        """모든 권한을 조회합니다."""
        return permission_query_crud.get_multi(db, skip=skip, limit=limit)

permission_query_service = PermissionQueryService()
