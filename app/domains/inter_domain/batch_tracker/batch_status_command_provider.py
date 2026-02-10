from sqlalchemy.orm import Session
from app.domains.services.batch_tracking.services.batch_command_service import batch_command_service

class BatchStatusCommandProvider:
    def register_new_batch(self, db: Session, *, device_id: int, total_count: int) -> str:
        return batch_command_service.initialize_batch(db, device_id=device_id, total_count=total_count)

    def mark_item_processed(self, db: Session, *, batch_id: str):
        return batch_command_service.increment_processed_count(db, batch_id=batch_id)

batch_status_command_provider = BatchStatusCommandProvider()