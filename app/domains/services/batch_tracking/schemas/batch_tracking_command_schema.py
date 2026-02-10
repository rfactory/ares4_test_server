from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BatchTrackingCreate(BaseModel):
    """배치 생성 시 필요한 입력 규격"""
    batch_id: str
    device_id: int
    total_count: int

class BatchTrackingUpdate(BaseModel):
    """상태 및 카운트 업데이트 규격"""
    processed_count: Optional[int] = None
    status: Optional[str] = None
    completed_at: Optional[datetime] = None