# --- Query-related Service ---
# 이 파일은 데이터의 상태를 변경하지 않는 'Query' 성격의 비즈니스 로직을 담당합니다.

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData
from ..crud.telemetry_query_crud import telemetry_crud_query
from ..schemas.telemetry_query import TelemetryFilter

class TelemetryQueryService:
    def get_telemetry_data(
        self, 
        db: Session, 
        *, 
        filters: TelemetryFilter,
        possession_start: Optional[datetime] = None, # Policy가 알려주는 소유 시작 시점
        possession_end: Optional[datetime] = None    # Policy가 알려주는 소유 종료 시점
    ) -> List[DBTelemetryData]:
        """필터 조건을 사용하여 텔레메트리 데이터를 조회합니다."""
        # 1. 사용자가 요청한 시작 시간이 소유 시작 시점보다 빠르면, 소유 시점으로 강제 보정
        if possession_start:
            if not filters.start_time or filters.start_time < possession_start:
                filters.start_time = possession_start
        
        # 2. 소유권이 이미 종료된 기기라면, 해제 시점 이후 데이터는 조회 불가 처리
        if possession_end:
            if not filters.end_time or filters.end_time > possession_end:
                filters.end_time = possession_end

        # 3. 보정된 시간 필터를 가지고 자신의 CRUD 호출
        return telemetry_crud_query.get_multiple_telemetry_data(
            db=db,
            skip=filters.skip,
            limit=filters.limit,
            device_ids=filters.device_ids,
            system_unit_ids=filters.system_unit_ids,
            snapshot_id=filters.snapshot_id,
            metric_names=filters.metric_names,
            start_time=filters.start_time,
            end_time=filters.end_time
        )

telemetry_query_service = TelemetryQueryService()
