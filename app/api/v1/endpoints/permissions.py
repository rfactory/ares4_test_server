from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, PermissionChecker # PermissionChecker 추가
from app.domains.inter_domain.permissions.schemas.permission_query import PermissionResponse # 스키마 임포트
from app.domains.inter_domain.permissions.permission_query_provider import permission_query_provider # 프로바이더 임포트

router = APIRouter()

@router.get(
    "",
    response_model=List[PermissionResponse],
    dependencies=[Depends(PermissionChecker("permission:read"))] # 권한 적용
)
async def get_permissions(db: Session = Depends(get_db)) -> List[PermissionResponse]:
    """
    권한 목록을 조회합니다.
    """
    permissions = permission_query_provider.get_all_permissions(db)
    return permissions
