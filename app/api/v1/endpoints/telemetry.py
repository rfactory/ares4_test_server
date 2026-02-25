from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.dependencies import get_db, get_active_context, ActiveContext
from app.domains.services.telemetry.schemas.telemetry_query import TelemetryFilter
from app.domains.inter_domain.policies.telemetry.telemetry_policy_provider import telemetry_policy_provider

router = APIRouter()

@router.get("/data", response_model=List[Any], status_code=status.HTTP_200_OK)
async def get_telemetry_data(
    *,
    db: Session = Depends(get_db),
    active_context: ActiveContext = Depends(get_active_context),
    filters: TelemetryFilter = Depends()
) -> Any:
    """
    ### [Scenario A] 텔레메트리 데이터 조회 (개인정보 격리 적용)
    
    Ares4 v3.0의 권한 체계에 따라 데이터를 조회합니다.
    - **전역 조회**: 'telemetry:read_all' 권한을 가진 Role(관리자급)은 전체 이력을 조회합니다.
    - **사용자 조회**: 권한이 없는 일반 Role은 본인이 가구를 소유했던 기간(`created_at` ~ `unassigned_at`)의 데이터만 볼 수 있습니다.
    - **보안**: 타인의 데이터나 소유권 이전 전후의 데이터는 원천적으로 차단됩니다.
    - **무결성**: 오직 읽기 전용이며, 기기 이외의 주체에 의한 데이터 조작은 불가합니다.
    """
    # Inter-Domain Provider 호출
    return telemetry_policy_provider.fetch_data(
        db=db,
        actor_user=active_context.user,
        filters=filters,
        active_role_id=active_context.active_role_id
    )