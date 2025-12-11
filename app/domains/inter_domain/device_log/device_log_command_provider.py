from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.models.events_logs.device_log import DeviceLog
from app.domains.services.device_log.services.device_log_command_service import device_log_command_service
from app.domains.services.device_log.schemas.device_log_command import DeviceLogCreate

class DeviceLogCommandProvider:
    def create_device_log(
        self,
        db: Session,
        device_id: int,
        log_level: str,
        description: str,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> DeviceLog:
        obj_in = DeviceLogCreate(
            device_id=device_id,
            log_level=log_level,
            description=description,
            metadata_json=metadata_json
        )
        return device_log_command_service.create_log(db, obj_in=obj_in)

device_log_command_provider = DeviceLogCommandProvider()
