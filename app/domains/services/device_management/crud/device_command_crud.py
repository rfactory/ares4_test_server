# crud/device_command_crud.py
from sqlalchemy.orm import Session
from typing import Optional, Any

from app.core.crud_base import CRUDBase
from app.models.objects.device import Device
from ..schemas.device_command import DeviceCreate, DeviceUpdate

class CRUDDeviceCommand(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def create_with_id(self, db: Session, *, obj_in: DeviceCreate, current_id: Any) -> Device:
        """상위 계층에서 생성된 ID와 모든 정보를 포함하여 새로운 장치를 생성합니다."""
        
        # [핵심] obj_in 에 들어있는 모든 필수 데이터를 DB 모델에 매핑합니다.
        db_obj = Device(
            cpu_serial=obj_in.cpu_serial,
            hardware_blueprint_id=obj_in.hardware_blueprint_id,
            system_unit_id=obj_in.system_unit_id,
            current_uuid=obj_in.uuid,
            hmac_key_name=obj_in.hmac_key_name,
            status=obj_in.status,
            is_active=True
        )
        
        db.add(db_obj)
        db.flush() 
        return db_obj

    def remove(self, db: Session, *, id: int) -> Device:
        """장치를 비활성화하여 소프트 삭제합니다."""
        db_obj = self.get(db, id=id) 
        db_obj.is_active = False
        db.add(db_obj)
        return db_obj

device_command_crud = CRUDDeviceCommand(Device)