from sqlalchemy.orm import Session

from app.models.events_logs.device_log import DeviceLog
from ..crud.device_log_command_crud import device_log_command_crud
from ..schemas.device_log_command import DeviceLogCreate

class DeviceLogCommandService:
    def create_log(self, db: Session, *, obj_in: DeviceLogCreate) -> DeviceLog:
        return device_log_command_crud.create(db, obj_in=obj_in)

device_log_command_service = DeviceLogCommandService()
