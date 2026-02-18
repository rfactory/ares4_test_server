from fastapi import APIRouter, Request, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.dependencies import get_db, get_current_user
from app.core.exceptions import AuthenticationError, AppLogicError, ValidationError, NotFoundError
from app.domains.inter_domain.policies.factory_enrollment.factory_enrollment_policy_provider import factory_enrollment_policy_provider
from app.models.objects.user import User

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
# 2. 사용자 기기 점유
# ---------------------------------------------------------
@router.post("/claim", status_code=status.HTTP_200_OK)
def claim_device(
    *,
    db: Session = Depends(get_db),
    # 이 Depends가 작동하면서 로그인하지 않은 유저는 자동으로 401 에러를 내뱉고 차단합니다.
    current_user: User = Depends(get_current_user), 
    token: str = Body(..., embed=True)
) -> Any:
    policy = factory_enrollment_policy_provider.get_policy()

    try:
        # 인증된 유저의 ID(current_user.id)를 정책에 넘겨줍니다.
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