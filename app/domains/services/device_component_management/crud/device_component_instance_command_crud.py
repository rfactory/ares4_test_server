from app.core.crud_base import CRUDBase
from app.models.relationships.device_component_instance import DeviceComponentInstance
from ..schemas.device_component_instance_command import DeviceComponentInstanceCreate
from pydantic import BaseModel # Placeholder for Update schema

# Update 스키마를 위한 임시 플레이스홀더
class DeviceComponentInstanceUpdate(BaseModel):
    pass

class CRUDDeviceComponentInstanceCommand(CRUDBase[DeviceComponentInstance, DeviceComponentInstanceCreate, DeviceComponentInstanceUpdate]):
    """장치-부품 연결 인스턴스의 생성, 수정, 삭제를 담당합니다."""
    pass

device_component_instance_command_crud = CRUDDeviceComponentInstanceCommand(DeviceComponentInstance)
