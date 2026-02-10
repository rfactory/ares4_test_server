import logging
import uuid
from sqlalchemy.orm import Session
from datetime import datetime

from ..crud.batch_tracking_command_crud import batch_tracking_command_crud
from ..crud.batch_tracking_query_crud import batch_tracking_query_crud
from ..schemas.batch_tracking_command_schema import BatchTrackingCreate

logger = logging.getLogger(__name__)

class BatchCommandService:
    def initialize_batch(self, db: Session, *, device_id: int, total_count: int) -> str:
        """새로운 배치를 생성하고 UUID 식별자를 반환합니다."""
        batch_uuid = str(uuid.uuid4())
        
        batch_tracking_command_crud.create(
            db, 
            obj_in=BatchTrackingCreate(
                batch_id=batch_uuid,
                device_id=device_id,
                total_count=total_count
            )
        )
        
        logger.info(f"📝 [Batch Tracker] Initialized: {batch_uuid} for Device {device_id} (Total: {total_count})")
        return batch_uuid
        
    def increment_processed_count(self, db: Session, *, batch_id: str):
        """항목 처리 완료를 기록하고, 필요 시 전체 완료 상태로 전환합니다."""
        # 1. 원자적 카운트 증가
        batch_tracking_command_crud.atomic_increment(db, batch_id=batch_id)
        
        # 2. 완료 여부 확인 및 상태 갱신 (지휘관 로직)
        batch = batch_tracking_query_crud.get_by_batch_id(db, batch_id=batch_id)
        if batch and batch.processed_count >= batch.total_count:
            batch_tracking_command_crud.mark_complete(db, batch_id=batch_id)
            logger.info(f"🚩 [Batch Tracker] Batch {batch_id} fully COMPLETED.")

batch_command_service = BatchCommandService()