from typing import Optional
from sqlalchemy.orm import Session
from ..crud.observation_snapshot_query_crud import observation_snapshot_crud_query
from app.models.events_logs.observation_snapshot import ObservationSnapshot

class ObservationSnapshotQueryService:
    def get_snapshot(self, db: Session, snapshot_id: str) -> Optional[ObservationSnapshot]:
        return observation_snapshot_crud_query.get(db, id=snapshot_id)

observation_snapshot_query_service = ObservationSnapshotQueryService()