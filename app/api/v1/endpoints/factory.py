from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.core.exceptions import AuthenticationError, AppLogicError
from app.domains.inter_domain.policies.factory_enrollment.factory_enrollment_policy_provider import factory_enrollment_policy_provider

router = APIRouter()

@router.post("/auto-enroll")
async def factory_auto_enroll(
    request: Request, 
    db: Session = Depends(get_db)
):
    body = await request.json()
    
    # 1. 라즈베리파이가 보고한 IP 추출
    target_ip = body.get("reported_ip")

    # 2. 공장 신뢰 IP 리스트 (현재 라즈베리파이 IP인 10.1.1.63을 직접 추가!)
    # 문자열 그대로 비교하기 때문에 정확한 IP를 넣어줘야 합니다.
    TRUSTED_FACTORY_IPS = ["127.0.0.1", "10.1.2.135"] 

    print(f"🔍 [DEBUG] Final Check - Target IP: {target_ip} against {TRUSTED_FACTORY_IPS}")

    policy = factory_enrollment_policy_provider.get_policy()

    try:
        # 3. Policy 실행
        result_data = await policy.execute_factory_enrollment(
            db=db,
            client_ip=target_ip,
            cpu_serial=body.get("cpu_serial"),
            trusted_ips=TRUSTED_FACTORY_IPS
        )
        return result_data

    except AuthenticationError as e:
        # 실패 시 로그를 더 자세히 찍어줍니다.
        print(f"❌ [Auth Error] {str(e)}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AppLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Factory enrollment failed: {e}")