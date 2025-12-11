from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

# --- AuditLogDetail 조회 응답용 스키마 ---

class AuditLogDetailBase(BaseModel):
    detail_key: str
    detail_value: str
    detail_value_type: str # SQLAlchemy 모델의 Enum 타입 반영 (예: 'STRING', 'INTEGER', 'JSON')
    description: Optional[str] = None

class AuditLogDetailResponse(AuditLogDetailBase):
    id: int
    audit_log_id: int # 부모 AuditLog에 대한 링크

    class Config:
        from_attributes = True # 이전 버전의 orm_mode = True 와 동일

# --- AuditLog 조회 응답용 스키마 ---

class AuditLogBase(BaseModel):
    event_type: str = "AUDIT" # SQLAlchemy 모델의 Enum 타입 반영 (예: 'DEVICE', 'AUDIT', 'CONSUMABLE_USAGE')
    log_level: Optional[str] = None # SQLAlchemy 모델의 Enum 타입 반영
    description: Optional[str] = None
    user_id: Optional[int] = None # 로그를 발생시킨 행위자 (NullableUserFKMixin)

class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime
    updated_at: datetime
    details_items: List[AuditLogDetailResponse] = [] # SQLAlchemy relationship 이름과 일치시키기 위해 'details'에서 변경

    class Config:
        from_attributes = True # 이전 버전의 orm_mode = True 와 동일
