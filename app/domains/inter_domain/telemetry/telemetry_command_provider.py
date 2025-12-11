# --- Telemetry Command Provider ---

from sqlalchemy.orm import Session
from typing import List

from app.domains.services.telemetry.schemas.telemetry_command import TelemetryCommandDataCreate
from app.domains.services.telemetry.services.telemetry_command_service import telemetry_command_service
from app.models.events_logs.telemetry_data import TelemetryData

class TelemetryCommandProvider:
    def create_multiple_telemetry_data(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        """Provides a stable interface to create multiple telemetry data records in bulk."""
        return telemetry_command_service.create_multiple_telemetry(db=db, obj_in_list=obj_in_list)

telemetry_command_provider = TelemetryCommandProvider()
