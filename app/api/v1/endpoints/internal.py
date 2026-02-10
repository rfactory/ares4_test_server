import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from app.dependencies import get_db
# 전용 정책 프로바이더 임포트
from app.domains.inter_domain.policies.system_management.internal_command_dispatch_policy_provider import internal_command_dispatch_policy_provider

logger = logging.getLogger(__name__)
router = APIRouter()

class DispatchCommandRequest(BaseModel):
    topic: str
    command: Dict[str, Any]

@router.post("/dispatch-command", status_code=status.HTTP_202_ACCEPTED)
async def dispatch_command(
    *,
    request_body: DispatchCommandRequest,
    db: Session = Depends(get_db),
):
    """
    내부 서비스용 MQTT 메시지 발행 엔드포인트.
    (Ares Aegis: 트랜잭션, 시스템 액터 식별, 감사 로그는 Policy에서 처리)
    """
    try:
        # 정책 지휘관에게 한 줄로 명령 하달
        return internal_command_dispatch_policy_provider.execute(
            db=db,
            topic=request_body.topic,
            command=request_body.command
        )
    except Exception as e:
        # 정책 내부에서 이미 롤백됨
        logger.error(f"Internal Command Dispatch Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to dispatch internal command."
        )