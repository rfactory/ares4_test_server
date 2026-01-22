from typing import List, Optional
from sqlalchemy.orm import Session

# 서비스는 절대 경로로 import
from app.domains.services.permissions.services.permission_query_service import permission_query_service

# 스키마는 상대 경로로 import
from .schemas.permission_query import PermissionResponse

class PermissionQueryProvider:
    def get_all_permissions(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[PermissionResponse]:
        permissions = permission_query_service.get_all_permissions(db, skip=skip, limit=limit)
        return [PermissionResponse.model_validate(p) for p in permissions]

    def get_permissions_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> List[str]:
        """특정 사용자가 주어진 컨텍스트에서 가지는 모든 권한의 이름 목록을 반환합니다."""
        permissions = permission_query_service.get_permissions_for_user_in_context(
            db=db, user_id=user_id, organization_id=organization_id
        )
        return [p.name for p in permissions]

permission_query_provider = PermissionQueryProvider()
