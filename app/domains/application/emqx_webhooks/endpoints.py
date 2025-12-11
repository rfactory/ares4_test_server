import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response # <-- Response import는 필수입니다.
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.domains.inter_domain.policies.emqx_auth_policy.provider import emqx_auth_policy_provider

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/auth")
async def mqtt_auth(request: Request, db: Session = Depends(get_db)):
    """
    EMQX HTTP 인증 웹훅 처리: 사용자 이름/비밀번호 인증.
    응답: {"result": "allow"} 또는 {"result": "deny"} (JSON)
    """
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            logger.warning("[Endpoint] Auth request missing username or password.")
            return JSONResponse(content={"result": "deny"}, status_code=400)

        is_authenticated = await emqx_auth_policy_provider.handle_auth(
            db, username=username, password=password
        )

        if is_authenticated:
            return JSONResponse(content={"result": "allow"})
        else:
            return JSONResponse(content={"result": "deny"})

    except Exception as e:
        logger.error(f"[Endpoint] Error in /auth: {e}", exc_info=True)
        return JSONResponse(content={"result": "deny"}, status_code=500)

@router.post("/acl")
async def mqtt_acl(request: Request, db: Session = Depends(get_db)):
    """
    EMQX HTTP 권한 부여(Authorization) 웹훅 처리: 토픽 접근 권한(ACL) 확인.
    응답: "1" (Plain Text, 허용) 또는 "2" (Plain Text, 거부)
    """
    try:
        body = await request.json()
        logger.info(f"[Endpoint] /acl called with body: {body}")
        username = body.get("username")
        client_id = body.get("clientid")
        topic = body.get("topic")
        access = body.get("access")

        if not all([username, client_id, topic, access]):
            logger.warning(f"[Endpoint] ACL request missing required fields: {body}")
            # 필드 누락 시 거부 (2)
            return Response(content="2", status_code=400, media_type="text/plain")

        is_authorized = await emqx_auth_policy_provider.handle_acl(
            db, username=username, client_id=client_id, topic=topic, access=access
        )

        if is_authorized:
            logger.info(f"[Endpoint] ACL check PASSED for client '{client_id}' on topic '{topic}'.")
            return JSONResponse(content={"result": "allow"}, status_code=200)
        else:
            logger.warning(f"[Endpoint] ACL check FAILED for client '{client_id}' on topic '{topic}'.")
            return JSONResponse(content={"result": "deny"}, status_code=200)

    except Exception as e:
        logger.error(f"[Endpoint] Error in /acl: {e}", exc_info=True)
        return JSONResponse(content={"result": "deny"}, status_code=500) # Internal Server Error

@router.post("/superuser")
async def mqtt_superuser(request: Request):
    """
    EMQX HTTP 슈퍼유저 웹훅 처리. 보안상 항상 거부합니다.
    응답: {"result": "deny"} (JSON)
    """
    body = await request.json()
    logger.warning(f"[Endpoint] Superuser check denied for: {body}")
    return JSONResponse(content={"result": "deny"})