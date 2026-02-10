import logging
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..crud.batch_tracking_query_crud import batch_tracking_query_crud

logger = logging.getLogger(__name__)

class BatchQueryService:
    def get_progress(self, db: Session, *, batch_id: str) -> Dict[str, Any]:
        """배치의 현재 진행 상황을 백분율로 산출합니다."""
        batch = batch_tracking_query_crud.get_by_batch_id(db, batch_id=batch_id)
        if not batch:
            return {"error": "Batch not found"}
        
        progress_pct = (batch.processed_count / batch.total_count) * 100 if batch.total_count > 0 else 0
        
        return{
            "batch_id": batch_id,
            "total": batch.total_count,
            "processed": batch.processed_count,
            "progress_percentage": round(progress_pct, 2),
            "status": batch.status
        }
    
    def is_purge_allowed(self, db: Session, *, batch_id: str) -> bool:
        """Ares Aegis 무결성 원칙: 100.0% 완료 및 COMPLETED 상태일 때만 삭제 허용"""
        batch = batch_tracking_query_crud.get_by_batch_id(db, batch_id=batch_id)
        if not batch:
            return False
            
        return batch.status == "COMPLETED" and batch.processed_count >= batch.total_count

batch_query_service = BatchQueryService()