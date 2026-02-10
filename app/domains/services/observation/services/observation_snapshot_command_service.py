from sqlalchemy.orm import Session
from ..crud.observation_snapshot_command_crud import observation_snapshot_crud_command
from ..schemas.observation_snapshot_command import ObservationSnapshotCreate
from app.models.events_logs.observation_snapshot import ObservationSnapshot

class ObservationSnapshotCommandService:
    def create_snapshot(self, db: Session, *, snapshot_id: str, system_unit_id: int, observation_type: str) -> ObservationSnapshot:
        obj_in = ObservationSnapshotCreate(id=snapshot_id, system_unit_id=system_unit_id, observation_type=observation_type)
        return observation_snapshot_crud_command.create(db, obj_in=obj_in)

observation_snapshot_command_service = ObservationSnapshotCommandService()