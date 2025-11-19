from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.supported_component import SupportedComponent
from app.models.relationships.device_component_instance import DeviceComponentInstance

class CRUDSupportedComponent:
    def get_by_component_type(self, db: Session, component_type: str) -> Optional[SupportedComponent]:
        return db.query(SupportedComponent).filter(SupportedComponent.component_type == component_type).first()

supported_component_crud = CRUDSupportedComponent()

class CRUDDeviceComponentInstance:
    def get_by_device_id_and_supported_component_id(
        self, db: Session, device_id: int, supported_component_id: int
    ) -> Optional[DeviceComponentInstance]:
        return db.query(DeviceComponentInstance).filter(
            DeviceComponentInstance.device_id == device_id,
            DeviceComponentInstance.supported_component_id == supported_component_id
        ).first()

device_component_instance_crud = CRUDDeviceComponentInstance()
