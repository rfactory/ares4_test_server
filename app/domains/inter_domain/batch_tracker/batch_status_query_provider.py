from sqlalchemy.orm import Session
from typing import Dict, Any
from app.domains.services.batch_tracking.services.batch_query_service import batch_query_service

class BatchStatusQueryProvider:
    def get_ingestion_progress(self, db: Session, *, batch_id: str) -> Dict[str, Any]:
        return batch_query_service.get_progress(db, batch_id=batch_id)

    def check_purge_permission(self, db: Session, *, batch_id: str) -> bool:
        return batch_query_service.is_purge_allowed(db, batch_id=batch_id)

batch_status_query_provider = BatchStatusQueryProvider()