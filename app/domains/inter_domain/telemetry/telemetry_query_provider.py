# --- Telemetry Query Provider ---

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from typing import Optional

from app.domains.services.telemetry.schemas.telemetry_query import TelemetryFilter
from app.domains.services.telemetry.services.telemetry_query_service import telemetry_query_service
from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData

class TelemetryQueryProvider:
    def get_telemetry_data(
        self, db: Session, *, 
        filters: TelemetryFilter,
        possession_start: Optional[datetime] = None, # 추가
        possession_end: Optional[datetime] = None    # 추가
    ) -> List[DBTelemetryData]:
        """Provides a stable interface to query telemetry data."""
        return telemetry_query_service.get_telemetry_data(
            db=db, 
            filters=filters,
            possession_start=possession_start, # 전달
            possession_end=possession_end      # 전달
        )

telemetry_query_provider = TelemetryQueryProvider()
