from typing import Optional
from sqlalchemy.orm import Session
from app.models.events_logs.batch_tracking import BatchTracking

class BatchTrackingQueryCRUD:
    def get_by_batch_id(self, db: Session, batch_id: str) -> Optional[BatchTracking]:
        """읽기 전용: 장부에서 배치를 찾아 반환합니다."""
        return db.query(BatchTracking).filter(BatchTracking.batch_id == batch_id).first()

batch_tracking_query_crud = BatchTrackingQueryCRUD()