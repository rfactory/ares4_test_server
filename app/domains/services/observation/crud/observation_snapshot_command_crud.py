from sqlalchemy.orm import Session
from app.models.events_logs.observation_snapshot import ObservationSnapshot
from ..schemas.observation_snapshot_command import ObservationSnapshotCreate

class CRUDObservationSnapshotCommand:
    def create(self, db: Session, *, obj_in: ObservationSnapshotCreate) -> ObservationSnapshot:
        db_obj = ObservationSnapshot(
            id=obj_in.id,
            system_unit_id=obj_in.system_unit_id,
            observation_type=obj_in.observation_type
        )
        db.add(db_obj)
        db.flush() # ID 확정 및 세션 등록 (Commit은 Policy에서)
        return db_obj

observation_snapshot_crud_command = CRUDObservationSnapshotCommand()