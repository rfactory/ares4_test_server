from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import logging
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mqtt")

@router.post("/auth")
async def mqtt_auth(request: Request, settings: Settings = Depends(get_settings)):
    try:
        body = await request.json()
        received_username = body.get("username", "None")
        received_password = body.get("password", "None")
        
        logger.info(f"[EMQX Auth] 수신값: username={received_username}")
        
        if received_username == settings.MQTT_USERNAME and received_password == settings.MQTT_PASSWORD:
            logger.info("[EMQX Auth] 인증 성공")
            return JSONResponse(content={"result": "allow"})
        else:
            logger.warning(f"[EMQX Auth] 인증 실패 - username: {received_username}")
            return JSONResponse(content={"result": "deny"})
    except Exception as e:
        logger.error(f"[EMQX Auth] 오류: {str(e)} - Raw body: {await request.body()}")
        return JSONResponse(content={"result": "deny"})

@router.post("/acl")
async def mqtt_acl(request: Request):
    try:
        body = await request.json()
        logger.info(f"[EMQX ACL] 수신값: {body}")
        return JSONResponse(content={"result": "allow"})
    except Exception as e:
        logger.error(f"[EMQX ACL] 오류: {str(e)} - Raw body: {await request.body()}")
        return JSONResponse(content={"result": "deny"})

@router.post("/superuser")
async def mqtt_superuser(request: Request):
    return JSONResponse(content={"result": "deny"})