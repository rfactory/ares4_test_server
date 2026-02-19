from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Any

from app.dependencies import get_db, get_active_context, ActiveContext
from app.models.objects.user import User

# 우리가 만든 Policy와 Schema 임포트
from app.domains.action_authorization.policies.system_unit_binding.system_unit_binding_policy import system_unit_binding_policy
from app.domains.services.system_unit.schemas.system_unit_command import DeviceBindingRequest

router = APIRouter()

@router.post("/bind-device", status_code=status.HTTP_200_OK)
def bind_device_to_unit(
    *,
    db: Session = Depends(get_db),
    active_context: ActiveContext = Depends(get_active_context), # 수정됨
    request_in: DeviceBindingRequest
) -> Any:
    """
    ### [Scenario C] 장치와 시스템 유닛 결합
    
    특정 기기를 유닛에 귀속시키고, 설계도에 정의된 핀맵을 실체화합니다.
    - **모든 기기가 충족되면 유닛은 ACTIVE 상태가 됩니다.**
    - **중복 마스터나 수용량 초과는 Validator에서 차단됩니다.**
    """
    result = system_unit_binding_policy.bind_device_to_unit(
        db=db,
        actor_user=active_context.user, 
        unit_id=request_in.unit_id,
        device_id=request_in.device_id,
        role=request_in.role
    )
    
    return result