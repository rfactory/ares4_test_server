from sqlalchemy.orm import Session
from app.domains.services.observation.services.observation_snapshot_command_service import observation_snapshot_command_service
from app.domains.services.observation.services.observation_snapshot_query_service import observation_snapshot_query_service
from .schemas.observation_snapshot_query import ObservationSnapshotRead

class ObservationSnapshotCommandProvider:
    def get_or_create_snapshot(
        self, 
        db: Session, 
        *, 
        snapshot_id: str, 
        system_unit_id: int, 
        observation_type: str = "TELEMETRY" 
    ) -> ObservationSnapshotRead:
        """
        [핵심 로직] 스냅샷이 있으면 가져오고 없으면 생성하여 반환합니다.
        다양한 프로토콜(MQTT/HTTP)의 동기화 지점 역할을 수행합니다.
        """
        # 1. 먼저 조회 (Query Service)
        snapshot_model = observation_snapshot_query_service.get_snapshot(db, snapshot_id)
        
        # 2. 없으면 생성 (Command Service)
        if not snapshot_model:
            snapshot_model = observation_snapshot_command_service.create_snapshot(
                db,
                snapshot_id=snapshot_id,
                system_unit_id=system_unit_id,
                observation_type=observation_type
            )
            
        return ObservationSnapshotRead.model_validate(snapshot_model)

observation_snapshot_command_provider = ObservationSnapshotCommandProvider()