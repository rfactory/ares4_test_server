from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class BatchTrackingResponse(BaseModel):
    """외부(API/Dashboard) 노출용 출력 규격"""
    batch_id: str
    device_id: int
    total_count: int
    processed_count: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)