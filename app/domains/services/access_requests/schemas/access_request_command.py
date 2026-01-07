# 1. app/domains/services/access_requests/schemas/access_request_command.py
from typing import Optional
from pydantic import BaseModel, Field, PositiveInt, EmailStr

class AccessRequestCreate(BaseModel):
    """새로운 접근 요청 생성을 위한 스키마."""
    reason: Optional[str] = Field(None, max_length=1000)  # 요청 사유
    requested_role_id: PositiveInt                        # 요청된 역할 ID
    organization_id: Optional[PositiveInt] = Field(None)  # 기업 요청이면 조직 ID, 개인이면 null

    model_config = {"extra": "forbid"}


class AccessRequestUpdate(BaseModel):
    """접근 요청 상태(승인/거절) 업데이트를 위한 스키마."""
    status: str
    reviewed_by_user_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    verification_code: Optional[str] = None
    verification_code_expires_at: Optional[str] = None


class AccessRequestInvite(BaseModel):
    """관리자가 사용자를 역할에 초대(push)하기 위한 스키마."""
    email_to_invite: EmailStr
    role_id: PositiveInt
    organization_id: Optional[PositiveInt] = None
    reason: Optional[str] = Field(None, max_length=1000)


class AcceptInvitationRequest(BaseModel):
    """사용자가 초대를 수락하기 위한 스키마."""
    verification_code: str = Field(..., min_length=6, max_length=6) # 6자리 인증 코드