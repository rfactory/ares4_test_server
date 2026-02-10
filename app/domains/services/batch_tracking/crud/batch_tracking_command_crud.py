from sqlalchemy.orm import Session
from sqlalchemy import update
from app.models.events_logs.batch_tracking import BatchTracking
from ..schemas.batch_tracking_command_schema import BatchTrackingCreate

class BatchTrackingCommandCRUD:
    def create(self, db: Session, *, obj_in: BatchTrackingCreate) -> BatchTracking:
        db_obj = BatchTracking(
            batch_id=obj_in.batch_id,
            device_id=obj_in.device_id,
            total_count=obj_in.total_count,
            status="PROCESSING"
        )
        db.add(db_obj)
        db.flush()
        return db_obj

    def atomic_increment(self, db: Session, batch_id: str):
        """DB 레벨 원자적 연산으로 Race Condition 방지"""
        db.execute(
            update(BatchTracking)
            .where(BatchTracking.batch_id == batch_id)
            .values(processed_count=BatchTracking.processed_count + 1)
        )

batch_tracking_command_crud = BatchTrackingCommandCRUD()