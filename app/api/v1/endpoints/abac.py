from typing import List
from fastapi import APIRouter, Depends

from app.dependencies import PermissionChecker
from app.domains.inter_domain.abac.abac_query_provider import abac_query_provider
from app.domains.services.abac.schemas.abac_query import AbacVariableResponse

router = APIRouter()

@router.get(
    "/variables",
    response_model=List[AbacVariableResponse],
    dependencies=[Depends(PermissionChecker("permission:read"))] # ABAC 변수도 권한의 일부로 간주
)
async def get_abac_variables() -> List[AbacVariableResponse]:
    """
    ABAC 규칙의 필터 조건 값으로 사용할 수 있는 동적 변수 목록을 조회합니다.
    """
    return abac_query_provider.get_abac_variables()
