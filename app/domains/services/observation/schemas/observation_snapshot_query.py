from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ObservationSnapshotRead(BaseModel):
    id: str
    system_unit_id: int
    observation_type: str
    created_at: datetime
    captured_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)