from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Any

from app.dependencies import get_db, get_active_context, ActiveContext, PermissionChecker

# 우리가 함께 만든 Policy와 Schema (해당 파일들에 존재함을 확인)
from app.domains.action_authorization.policies.system_unit_binding.system_unit_binding_policy import system_unit_binding_policy
from app.domains.services.system_unit.schemas.system_unit_command import DeviceBindingRequest

router = APIRouter()

@router.post("/bind-device", status_code=status.HTTP_200_OK)
async def bind_device_to_unit(
    *,
    db: Session = Depends(get_db),
    # 프로젝트 표준인 ActiveContext를 통해 로그인 세션 및 조직 정보를 확보합니다.
    active_context: ActiveContext = Depends(get_active_context),
    # 유닛 관리 권한이 있는 사용자만 접근 가능하도록 설정합니다.
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
    result = system_unit_binding_policy.bind_device_to_unit(
        db=db,
        actor_user=active_context.user, 
        unit_id=request_in.unit_id,
        device_id=request_in.device_id,
        role=request_in.role
    )
    
    return result