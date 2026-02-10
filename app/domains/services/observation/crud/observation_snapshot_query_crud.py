from typing import Optional
from sqlalchemy.orm import Session
from app.models.events_logs.observation_snapshot import ObservationSnapshot

class CRUDObservationSnapshotQuery:
    def get(self, db: Session, id: str) -> Optional[ObservationSnapshot]:
        return db.query(ObservationSnapshot).filter(ObservationSnapshot.id == id).first()

observation_snapshot_crud_query = CRUDObservationSnapshotQuery()