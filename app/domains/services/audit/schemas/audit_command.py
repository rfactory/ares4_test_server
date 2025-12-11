from typing import List, Optional
from pydantic import BaseModel

# --- AuditLogDetail 생성 관련 스키마 ---

class AuditLogDetailBase(BaseModel):
    detail_key: str
    detail_value: str
    detail_value_type: str # SQLAlchemy 모델의 Enum 타입 반영 (예: 'STRING', 'INTEGER', 'JSON')
    description: Optional[str] = None

class AuditLogDetailCreate(AuditLogDetailBase):
    pass

# --- AuditLog 생성 관련 스키마 ---

class AuditLogBase(BaseModel):
    event_type: str = "AUDIT" # SQLAlchemy 모델의 Enum 타입 반영 (예: 'DEVICE', 'AUDIT', 'CONSUMABLE_USAGE')
    log_level: Optional[str] = None # SQLAlchemy 모델의 Enum 타입 반영
    description: Optional[str] = None
    user_id: Optional[int] = None # 로그를 발생시킨 행위자 (NullableUserFKMixin)

class AuditLogCreate(AuditLogBase):
    details: List[AuditLogDetailCreate] = [] # 상세 항목 리스트
