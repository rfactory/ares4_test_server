from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Any

from app.dependencies import get_db, get_active_context, ActiveContext, PermissionChecker

# 우리가 함께 만든 Policy와 Schema (해당 파일들에 존재함을 확인)
from app.domains.inter_domain.policies.system_unit.system_unit_policy_provider import system_unit_policy_provider
from app.domains.services.system_unit.schemas.system_unit_command import DeviceBindingRequest

router = APIRouter()

@router.post("/bind-device", status_code=status.HTTP_200_OK)
async def bind_device_to_unit(
    *,
    db: Session = Depends(get_db),
    active_context: ActiveContext = Depends(get_active_context),
    _permission: None = Depends(PermissionChecker(required_permission="system_units:manage")),
    request_in: DeviceBindingRequest
) -> Any:
    """
    ### [Scenario C] 장치와 시스템 유닛 결합
    
    특정 기기를 유닛에 귀속시키고, 설계도에 정의된 핀맵을 복제하여 실체화합니다.
    - **검증**: 사용자 소유권, 유닛 수용량, 마스터 중복 여부를 Validator에서 판단합니다.
    - **완결성**: 설계도 수량이 모두 충족되면 유닛은 자동으로 'ACTIVE' 상태가 됩니다.
    - **보안**: 'system_units:manage' 권한이 필요합니다.
    """
    # active_context.user는 app/models/objects/user.py의 User 모델 인스턴스입니다.
    result = system_unit_policy_provider.bind_device(
        db=db,
        actor_user=active_context.user, 
        unit_id=request_in.unit_id,
        device_id=request_in.device_id,
        role=request_in.role
    )
    
    return result

@router.post("/{unit_id}/unbind-owner", status_code=status.HTTP_200_OK)
async def unbind_unit_owner(
    unit_id: int,
    db: Session = Depends(get_db),
    active_context: ActiveContext = Depends(get_active_context),
    # 소유권을 해제하는 행위도 관리 권한이 필요하므로 동일한 권한 체크를 적용합니다.
    _permission: None = Depends(PermissionChecker(required_permission="system_units:manage")),
) -> Any:
    """
    ### [Scenario A] 시스템 유닛 소유권 해제 (Unbind)
    
    현재 사용자와 시스템 유닛의 소유 관계를 안전하게 종료(Soft Unbind)합니다.
    - **데이터**: 기록은 삭제하지 않고 `unassigned_at` 시점만 기록하여 이력을 보존합니다.
    - **영향**: 해당 주인이 초대했던 운영자 및 조회자들의 권한도 함께 자동으로 종료됩니다.
    - **상태**: 유닛은 기기 연결을 유지한 채 '새 주인 대기(PENDING_OWNER)' 상태가 됩니다.
    - **보안**: 'system_units:manage' 권한이 필요합니다.
    """
    # Policy 호출 (Orchestration)
    result = system_unit_policy_provider.unbind_owner(
        db=db,
        actor_user=active_context.user,
        unit_id=unit_id
    )
    
    return result