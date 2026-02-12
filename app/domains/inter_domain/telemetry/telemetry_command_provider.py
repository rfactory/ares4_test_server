# --- Telemetry Command Provider ---

from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.domains.services.telemetry.schemas.telemetry_command import TelemetryCommandDataCreate
from app.domains.services.telemetry.services.telemetry_command_service import telemetry_command_service
from app.models.events_logs.telemetry_data import TelemetryData

class TelemetryCommandProvider:
    def create_multiple_telemetry_data(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        """Provides a stable interface to create multiple telemetry data records in bulk."""
        return telemetry_command_service.create_multiple_telemetry(db=db, obj_in_list=obj_in_list)
    
    def bulk_upsert_telemetry_data(self, db: Session, *, device_id: int, telemetry_list: List[Dict]) -> int:
        """
        [Ares Aegis] 대용량 배치 전송 전용 고속 인터페이스.
        - Dict 리스트를 받아 중복을 스킵하며 초고속으로 저장합니다.
        """
        return telemetry_command_service.bulk_upsert_telemetry(
            db=db, 
            device_id=device_id, 
            telemetry_list=telemetry_list
        )
    
    def process_cluster_batch_ingestion(self, db: Session, *, system_unit, payload: Dict[str, Any]):
        """클러스터 단위의 통합 데이터를 분해하여 저장하도록 서비스에 명령합니다."""
        return telemetry_command_service.process_cluster_batch_ingestion(
            db=db, 
            system_unit=system_unit, 
            payload=payload
        )

telemetry_command_provider = TelemetryCommandProvider()
