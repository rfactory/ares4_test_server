from fastapi import APIRouter, Request, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Any

from app.dependencies import get_db
from app.core.exceptions import AuthenticationError, AppLogicError, ValidationError, NotFoundError
from app.domains.inter_domain.policies.factory_enrollment.factory_enrollment_policy_provider import factory_enrollment_policy_provider

# [확인 필요] 사용자 인증용 함수가 어디에 있나요? 
# 보통 app.dependencies에 같이 있거나 auth 쪽에 있을 겁니다. 일단 임시로 적어둡니다.
# from app.dependencies import get_current_active_user

router = APIRouter()

# ---------------------------------------------------------
# 1. 기기 자동 등록 (기존 로직 유지)
# ---------------------------------------------------------
@router.post("/auto-enroll")
async def factory_auto_enroll(
    request: Request, 
    db: Session = Depends(get_db)
):
    body = await request.json()
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
# 2. 사용자 기기 점유 (신규 추가)
# ---------------------------------------------------------
@router.post("/claim")
def claim_device(
    *,
    db: Session = Depends(get_db),
    # [주의] 이 부분은 로그인한 유저의 정보를 가져오는 함수가 필요합니다.
    # 다니엘님의 프로젝트에서 현재 로그인 유저를 가져오는 함수명을 알려주시면 바로 바꿀게요!
    current_user_id: int = 1, # 우선 테스트를 위해 임시로 1번 유저로 세팅
    token: str = Body(..., embed=True)
) -> Any:
    policy = factory_enrollment_policy_provider.get_policy()

    try:
        result = policy.claim_unit(
            db=db,
            token_value=token,
            claimer_user_id=current_user_id
        )
        return result
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Claim failed.")