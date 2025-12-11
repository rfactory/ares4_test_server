# inter_domain/device_component_management/device_component_command_provider.py

from sqlalchemy.orm import Session

# --- Service Imports ---
from app.domains.services.device_component_management.services.device_component_instance_command_service import device_component_instance_command_service

# --- Schema and Model Imports ---
from app.domains.services.device_component_management.schemas.device_component_instance_command import DeviceComponentInstanceCreate
from app.models.relationships.device_component_instance import DeviceComponentInstance
from app.models.objects.user import User

class DeviceComponentCommandProvider:
    """
    장치-부품 연결(Device Component Instance) 관련 Command 서비스의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def attach_component_to_device(self, db: Session, *, obj_in: DeviceComponentInstanceCreate, actor_user: User) -> DeviceComponentInstance:
        return device_component_instance_command_service.attach_component_to_device(db=db, obj_in=obj_in, actor_user=actor_user)

    def detach_component_from_device(self, db: Session, *, device_id: int, supported_component_id: int, instance_name: str, actor_user: User) -> DeviceComponentInstance:
        return device_component_instance_command_service.detach_component_from_device(
            db=db, device_id=device_id, supported_component_id=supported_component_id, instance_name=instance_name, actor_user=actor_user
        )

device_component_command_provider = DeviceComponentCommandProvider()
