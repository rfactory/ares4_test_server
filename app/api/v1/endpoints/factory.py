from fastapi import APIRouter, Request, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app.dependencies import get_db, get_current_user
from app.core.exceptions import AuthenticationError, AppLogicError, ValidationError, NotFoundError, PermissionDeniedError
from app.domains.inter_domain.policies.factory_enrollment.factory_enrollment_policy_provider import factory_enrollment_policy_provider
from app.domains.inter_domain.policies.system_unit.system_unit_policy_provider import system_unit_policy_provider
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_query_provider import system_unit_assignment_query_provider

# [타입 힌팅용 임포트]
from app.models.objects.user import User
from app.models.objects.device import Device as DBDevice
from app.models.relationships.system_unit_assignment import SystemUnitAssignment

router = APIRouter()

# ---------------------------------------------------------
# 1. 기기 자동 등록 (기존 로직 유지)
# ---------------------------------------------------------
@router.post("/auto-enroll")
async def factory_auto_enroll(
    request: Request, 
    db: Session = Depends(get_db)
):
    body: Dict[str, Any] = await request.json()
    target_ip = body.get("reported_ip")
    TRUSTED_FACTORY_IPS = ["127.0.0.1", "10.1.1.63"] 

    policy = factory_enrollment_policy_provider.get_policy()

    try:
        result_data = await policy.execute_factory_enrollment(
            db=db,
            client_ip=target_ip,
            cpu_serial=body.get("cpu_serial"),
            trusted_ips=TRUSTED_FACTORY_IPS
        )
        return result_data
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {e}")
    
# ---------------------------------------------------------
# 2. 사용자 기기 점유 (QR 스캔)
# ---------------------------------------------------------
@router.post("/claim", status_code=status.HTTP_200_OK)
def claim_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), 
    token: str = Body(..., embed=True)
) -> Any:
    policy = factory_enrollment_policy_provider.get_policy()

    try:
        result = policy.claim_unit(
            db=db,
            token_value=token,
            claimer_user_id=current_user.id 
        )
        return result
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Claim failed.")

# ---------------------------------------------------------
# 3. 기기 최종 핸드셰이크 (WiFi 연결 후 등록)
# ---------------------------------------------------------
@router.post("/handshake", status_code=status.HTTP_200_OK)
def device_handshake(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cpu_serial: str = Body(...),
    device_uuid: str = Body(...)
) -> Any:
    # 1. 각 도메인 정책 지휘관 확보
    enroll_policy = factory_enrollment_policy_provider.get_policy()
    bind_policy = system_unit_policy_provider.get_policy()

    try:
        # 2. 기기 정체성 확인 (Enrollment Policy)
        # 여기서 반환 타입을 DBDevice로 명시했으므로 device_obj.id에 색상이 나옵니다.
        device_obj: DBDevice = enroll_policy.verify_device_identity_or_raise(
            db, cpu_serial=cpu_serial, device_uuid=device_uuid
        )

        # 3. 사용자가 점유 중인 유닛 확인 (Assignment Domain)
        # 반환 타입을 SystemUnitAssignment로 명시하여 .system_unit_id 에 색상을 입힙니다.
        assignment: SystemUnitAssignment = system_unit_assignment_query_provider.get_active_owner_assignment(
            db, user_id=current_user.id
        )
        if not assignment:
            raise AppLogicError("할당된 유닛이 없습니다. 먼저 가구의 QR 코드를 스캔하세요.")

        # 4. 정책 간 조율 (The Grand Orchestration)
        # 이제 bind_policy.을 치면 bind_device_to_unit 이 자동완성 됩니다.
        result = bind_policy.bind_device_to_unit(
            db, 
            actor_user=current_user, 
            unit_id=assignment.system_unit_id, 
            device_id=device_obj.id,
            role="MASTER"
        )
        
        return result

    except (PermissionDeniedError, AppLogicError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Handshake failed: {e}")