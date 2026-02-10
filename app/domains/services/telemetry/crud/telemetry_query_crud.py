# --- Query-related CRUD ---
# 이 파일은 데이터의 상태를 변경하지 않고 DB에서 데이터를 조회하는 'Query' CRUD 클래스를 정의합니다.

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData

class CRUDTelemetryQuery:
    def get_multiple_telemetry_data(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        device_ids: Optional[List[int]] = None,
        system_unit_ids: Optional[List[int]] = None, # [추가]
        snapshot_id: Optional[str] = None,           # [추가]
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[DBTelemetryData]:
        query = db.query(DBTelemetryData).options(joinedload(DBTelemetryData.device))

        if device_ids:
            query = query.filter(DBTelemetryData.device_id.in_(device_ids))
        if system_unit_ids: # [추가]
            query = query.filter(DBTelemetryData.system_unit_id.in_(system_unit_ids))
        if snapshot_id:     # [추가]
            query = query.filter(DBTelemetryData.snapshot_id == snapshot_id)
        if metric_names:
            query = query.filter(DBTelemetryData.metric_name.in_(metric_names))
        
        # [수정] DB 모델의 실제 컬럼명(captured_at 또는 created_at)에 맞춥니다.
        if start_time:
            query = query.filter(DBTelemetryData.captured_at >= start_time)
        if end_time:
            query = query.filter(DBTelemetryData.captured_at <= end_time)
        
        return query.order_by(DBTelemetryData.captured_at.desc()).offset(skip).limit(limit).all()

telemetry_crud_query = CRUDTelemetryQuery()
