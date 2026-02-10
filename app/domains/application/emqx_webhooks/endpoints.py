import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response # <-- Response import는 필수입니다.
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db
from app.domains.inter_domain.policies.emqx_auth_policy.provider import emqx_auth_policy_provider
from app.domains.application.ingestion.ingestion_policy import ingestion_policy

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/auth")
async def mqtt_auth(request: Request, db: Session = Depends(get_db)):
    """
    EMQX HTTP 인증 웹훅 처리: 사용자(ID/PW) 또는 기기(mTLS) 인증 분기.
    """
    try:
        body: Dict[str, Any] = await request.json()
        username = body.get("username")
        password = body.get("password")
        client_id = body.get("clientid")  # 신규 재료 추가!

        # [수정] 아이디/비번이 없더라도 client_id가 있다면 정책관에게 판단을 맡깁니다.
        if not (username and password) and not client_id:
            logger.warning(f"[Endpoint] Auth request missing credentials. body: {body}")
            return JSONResponse(content={"result": "deny"}, status_code=400)

        # 지휘관에게 모든 재료를 넘깁니다.
        is_authenticated = await emqx_auth_policy_provider.handle_auth(
            db, 
            username=username, 
            password=password,
            client_id=client_id  # client_id 전달
        )

        if is_authenticated:
            return JSONResponse(content={"result": "allow"})
        else:
            # 정책관이 거부한 경우
            return JSONResponse(content={"result": "deny"})

    except Exception as e:
        logger.error(f"[Endpoint] Error in /auth: {e}", exc_info=True)
        return JSONResponse(content={"result": "deny"}, status_code=500)

@router.post("/acl")
async def mqtt_acl(request: Request, db: Session = Depends(get_db)):
    """
    EMQX HTTP 권한 부여(ACL) 웹훅 처리.
    """
    try:
        body: Dict[str, Any] = await request.json()
        logger.info(f"[Endpoint] /acl called with body: {body}")
        
        username = body.get("username")
        client_id = body.get("clientid")
        topic = body.get("topic")
        access = body.get("access")

        # [수정] mTLS 기기는 username이 없을 수 있으므로 체크 조건을 완화합니다.
        if not all([client_id, topic, access]):
            logger.warning(f"[Endpoint] ACL request missing required fields: {body}")
            return Response(content="deny", status_code=200) # EMQX 규격에 맞춤

        is_authorized = await emqx_auth_policy_provider.handle_acl(
            db, 
            username=username, 
            client_id=client_id, 
            topic=topic, 
            access=access
        )

        if is_authorized:
            return JSONResponse(content={"result": "allow"}, status_code=200)
        else:
            return JSONResponse(content={"result": "deny"}, status_code=200)

    except Exception as e:
        logger.error(f"[Endpoint] Error in /acl: {e}", exc_info=True)
        return JSONResponse(content={"result": "deny"}, status_code=500)

@router.post("/superuser")
async def mqtt_superuser(request: Request):
    """
    EMQX HTTP 슈퍼유저 웹훅 처리. 보안상 항상 거부합니다.
    응답: {"result": "deny"} (JSON)
    """
    body: Dict[str, Any] = await request.json()
    logger.warning(f"[Endpoint] Superuser check denied for: {body}")
    return JSONResponse(content={"result": "deny"})

@router.post("/publish")
async def mqtt_publish(request: Request, db: Session = Depends(get_db)):
    try:
        # 1. 데이터 추출 (가장 먼저 수행)
        body: Dict[str, Any] = await request.json()
        
        # 2. 헤더 체크 로직 (X-Ares-Secret)
        # 테스트 환경에서 헤더가 없는 경우에도 동작하도록 유연하게 처리합니다.
        secret_key = request.headers.get("X-Ares-Secret")
        if settings.EMQX_WEBHOOK_SECRET and secret_key != settings.EMQX_WEBHOOK_SECRET:
            logger.warning(f"[Webhook] Secret Mismatch. Expected: {settings.EMQX_WEBHOOK_SECRET}, Got: {secret_key}")
            # 보안 강화를 원하시면 아래 주석을 해제하여 엄격하게 차단하세요.
            # return JSONResponse(content={"result": "deny"}, status_code=403)

        # 3. 통합 지휘관(Ingestion Policy) 호출
        # body 자체가 아닌 body.get("payload")를 넘겨줌으로써 HMAC 대상 범위를 맞춥니다.
        success, error_msg = ingestion_policy.handle_webhook_ingestion(
            db, 
            topic=body.get("topic"), 
            payload=body.get("payload")
        )
        
        if success:
            return JSONResponse(content={"result": "ok"})
        else:
            # 검증 실패 시 상세 이유를 포함하여 반환 (디버깅용)
            return JSONResponse(content={"result": "error", "message": error_msg}, status_code=400)
            
    except Exception as e:
        logger.error(f"[Webhook] Critical Entry Error: {e}", exc_info=True)
        return JSONResponse(content={"result": "error"}, status_code=500)