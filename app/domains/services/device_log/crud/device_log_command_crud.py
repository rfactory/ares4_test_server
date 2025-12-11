from sqlalchemy.orm import Session
from app.models.events_logs.device_log import DeviceLog
from ..schemas.device_log_command import DeviceLogCreate

class CRUDDeviceLogCommand:
    def create(self, db: Session, *, obj_in: DeviceLogCreate) -> DeviceLog:
        db_obj = DeviceLog(
            device_id=obj_in.device_id,
            event_type='DEVICE', # DeviceLog의 기본값
            log_level=obj_in.log_level,
            description=obj_in.description,
            metadata_json=obj_in.metadata_json
        )
        db.add(db_obj)
        # db.commit() # 커밋은 서비스/애플리케이션 계층에서 처리
        # db.refresh(db_obj) # 새로고침은 서비스/애플리케이션 계층에서 처리
        return db_obj

device_log_command_crud = CRUDDeviceLogCommand()
