# 1. app/domains/services/access_requests/schemas/access_request_command.py
from typing import Optional
from pydantic import BaseModel, Field, PositiveInt

class AccessRequestCreate(BaseModel):
    """새로운 접근 요청 생성을 위한 스키마."""
    reason: Optional[str] = Field(None, max_length=1000)  # 요청 사유
    requested_role_id: PositiveInt                        # 요청된 역할 ID
    organization_id: Optional[PositiveInt] = Field(None)  # 기업 요청이면 조직 ID, 개인이면 null

    model_config = {"extra": "forbid"}


class AccessRequestUpdate(BaseModel):
    """접근 요청 상태(승인/거절) 업데이트를 위한 스키마."""
    status: str = Field(..., pattern="^(approved|rejected)$")
    rejection_reason: Optional[str] = Field(None, max_length=1000)