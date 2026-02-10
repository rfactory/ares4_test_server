import logging
from typing import List
from fastapi import APIRouter, Depends

from app.dependencies import PermissionChecker
from app.domains.inter_domain.common.schemas.common_query import ManageableResourceResponse
# 공식 창구(Provider) 임포트
from app.domains.inter_domain.common.common_resource_query_provider import common_resource_query_provider

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/manageable-resources",
    response_model=List[ManageableResourceResponse],
    dependencies=[Depends(PermissionChecker("permission:read"))]
)
async def get_manageable_resources() -> List[ManageableResourceResponse]:
    """
    [Common Query]
    ABAC 규칙 등에서 필터링 대상으로 지정할 수 있는 리소스(테이블) 및 컬럼 메타데이터를 조회합니다.
    Ares Aegis: 모든 내성(Inspection) 로직은 CommonResourceQueryProvider 내부로 격리되었습니다.
    """
    logger.info("Endpoint(Common): Requesting manageable resources metadata")
    
    # 지휘관은 명령만 내립니다. 실제 '삽질'은 Provider가 연결한 Service가 수행합니다.
    return common_resource_query_provider.fetch_manageable_resources()