from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.objects.permission import Permission
from ..crud.permission_query_crud import permission_query_crud

class PermissionQueryService:
    def get_all_permissions(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Permission]:
        """모든 권한을 조회합니다."""
        return permission_query_crud.get_multi(db, skip=skip, limit=limit)

    def get_permissions_for_user_in_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> List[Permission]:
        """특정 사용자가 주어진 컨텍스트에서 가지는 모든 권한을 조회합니다."""
        return permission_query_crud.get_permissions_for_user_in_context(
            db=db, user_id=user_id, organization_id=organization_id
        )

permission_query_service = PermissionQueryService()
