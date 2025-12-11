from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict # ConfigDict 추가

# 조회 관련 스키마

class AccessRequestRead(BaseModel):
    """접근 요청 조회 결과를 위한 스키마."""
    id: int = Field(..., description="접근 요청 고유 ID")
    user_id: int = Field(..., description="요청 대상 사용자 ID")
    requested_role_id: int = Field(..., description="요청된 역할 ID")
    organization_id: Optional[int] = Field(None, description="대상 조직 ID (기업용 요청인 경우)")
    status: str = Field(..., description="요청 상태 (pending, approved, rejected)")
    reason: Optional[str] = Field(None, description="요청 사유")
    # 추가 필드 (예: 생성 시간, 검토자 ID 등)는 필요에 따라 포함

    model_config = ConfigDict(from_attributes=True) # Pydantic v2 스타일로 변경

class AccessRequestQuery(BaseModel):
    """접근 요청 목록 필터링을 위한 스키마."""
    id: Optional[int] = Field(None, description="필터링할 접근 요청 ID")
    user_id: Optional[int] = Field(None, description="필터링할 사용자 ID")
    requested_role_id: Optional[int] = Field(None, description="필터링할 요청된 역할 ID")
    organization_id: Optional[int] = Field(None, description="필터링할 조직 ID")
    status: Optional[str] = Field("pending", description="필터링할 요청 상태 (기본값: pending)")
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")
