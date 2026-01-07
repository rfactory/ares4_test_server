from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AccessRequestRead(BaseModel):
    id: int
    user_id: int
    requested_role_id: int
    organization_id: Optional[int] = None
    reason: Optional[str] = None
    status: str
    type: str
    initiated_by_user_id: int
    created_at: datetime
    updated_at: datetime
    verification_code_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AccessRequestQuery(BaseModel):
    """접근 요청 목록 필터링을 위한 스키마."""
    id: Optional[int] = Field(None, description="필터링할 접근 요청 ID")
    user_id: Optional[int] = Field(None, description="필터링할 사용자 ID")
    requested_role_id: Optional[int] = Field(None, description="필터링할 요청된 역할 ID")
    organization_id: Optional[int] = Field(None, description="필터링할 조직 ID")
    status: Optional[str] = Field("pending", description="필터링할 요청 상태 (기본값: pending)")
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")
