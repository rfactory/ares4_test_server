# --- Query-related Service ---
# 이 파일은 데이터의 상태를 변경하지 않는 'Query' 성격의 비즈니스 로직을 담당합니다.

from sqlalchemy.orm import Session
from typing import List

from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData
from ..crud.telemetry_query_crud import telemetry_crud_query
from ..schemas.telemetry_query import TelemetryFilter

class TelemetryQueryService:
    def get_telemetry_data(self, db: Session, *, filters: TelemetryFilter) -> List[DBTelemetryData]:
        """필터 조건을 사용하여 텔레메트리 데이터를 조회합니다."""
        return telemetry_crud_query.get_multiple_telemetry_data(
            db=db,
            skip=filters.skip,
            limit=filters.limit,
            device_ids=filters.device_ids,
            metric_names=filters.metric_names,
            start_time=filters.start_time,
            end_time=filters.end_time
        )

telemetry_query_service = TelemetryQueryService()
