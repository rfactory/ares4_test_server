from typing import List
from sqlalchemy.orm import Session

# 서비스는 절대 경로로 import
from app.domains.services.permissions.services.permission_query_service import permission_query_service

# 스키마는 상대 경로로 import
from .schemas.permission_query import PermissionResponse

class PermissionQueryProvider:
    def get_all_permissions(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[PermissionResponse]:
        permissions = permission_query_service.get_all_permissions(db, skip=skip, limit=limit)
        return [PermissionResponse.model_validate(p) for p in permissions]

permission_query_provider = PermissionQueryProvider()
