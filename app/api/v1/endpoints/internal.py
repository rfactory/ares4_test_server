import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.dependencies import get_db
from app.models.objects.user import User
from app.domains.inter_domain.command_dispatch import command_dispatch_provider

logger = logging.getLogger(__name__)
router = APIRouter()

class DispatchCommandRequest(BaseModel):
    topic: str
    command: Dict[str, Any]
    # actor_user_id: Optional[int] # 내부 API이므로, actor를 어떻게 처리할지 정의 필요

@router.post("/dispatch-command", status_code=202)
def dispatch_command(
    *, 
    request_body: DispatchCommandRequest,
    db: Session = Depends(get_db),
    # internal_api_key: str = Depends(deps.get_internal_api_key) # 내부용 API Key 인증 추가 가능
):
    """
    내부 서비스에서 MQTT 메시지 발행을 요청하는 엔드포인트입니다.
    device-health-checker와 같은 다른 프로세스에서 이 API를 호출하여 메시지를 발행합니다.
    """
    logger.info(
        f"Internal API: Received request to dispatch command to topic: {request_body.topic}"
    )
    
    # 내부 API 호출의 경우 actor를 어떻게 정의할지 결정해야 합니다.
    # 여기서는 시스템 사용자(ID 1)를 사용하거나, 요청에 명시된 ID를 사용할 수 있습니다.
    # 우선은 시스템 사용자로 가정합니다.
    system_user = db.query(User).filter(User.id == 1).first()
    if not system_user:
        logger.warning("System user (ID 1) not found for internal API audit log.")

    command_dispatch_provider.publish_command(
        db=db, 
        topic=request_body.topic, 
        command=request_body.command, 
        actor_user=system_user
    )
    
    return {"message": "Command dispatch accepted."}
