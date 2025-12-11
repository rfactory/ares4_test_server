# services/device_component_instance_command_service.py

from sqlalchemy.orm import Session

# --- Model Imports ---
from app.models.objects.supported_component import SupportedComponent
from app.models.objects.device import Device
from app.models.objects.user import User
from app.models.relationships.device_component_instance import DeviceComponentInstance

# --- CRUD and Schema Imports ---
from ..crud.device_component_instance_command_crud import device_component_instance_command_crud
from ..crud.device_component_instance_query_crud import device_component_instance_query_crud
from ..schemas.device_component_instance_command import DeviceComponentInstanceCreate

# --- Provider and Exception Imports ---
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.core.exceptions import NotFoundError, DuplicateEntryError

class DeviceComponentInstanceCommandService:
    """장치-부품 연결 인스턴스의 생명주기를 관리합니다."""

    def attach_component_to_device(self, db: Session, *, obj_in: DeviceComponentInstanceCreate, actor_user: User) -> DeviceComponentInstance:
        """
        특정 장치에 부품 인스턴스를 연결(생성)합니다.
        """
        # 방어적 확인 1: device_id와 supported_component_id가 유효한지 확인
        if not db.query(Device).filter(Device.id == obj_in.device_id).first():
            raise NotFoundError("Device", str(obj_in.device_id))
        if not db.query(SupportedComponent).filter(SupportedComponent.id == obj_in.supported_component_id).first():
            raise NotFoundError("SupportedComponent", str(obj_in.supported_component_id))

        # 방어적 확인 2: 중복 연결 확인 (device_id, supported_component_id, instance_name의 조합이 unique해야 함)
        existing_instance = device_component_instance_query_crud.get_by_device_id_and_supported_component_id(
            db, device_id=obj_in.device_id, supported_component_id=obj_in.supported_component_id, instance_name=obj_in.instance_name
        )
        if existing_instance:
            raise DuplicateEntryError(
                resource_name="DeviceComponentInstance",
                field_name="device_id, supported_component_id, and instance_name",
                field_value=f"Device {obj_in.device_id} already has component {obj_in.supported_component_id} with name {obj_in.instance_name} attached."
            )

        new_instance = device_component_instance_command_crud.create(db, obj_in=obj_in)
        db.flush() # ID 발급을 위해 flush

        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="DeviceComponentInstance",
            resource_id=new_instance.id,
            new_value=new_instance.as_dict()
        )
        return new_instance

    def detach_component_from_device(self, db: Session, *, device_id: int, supported_component_id: int, instance_name: str, actor_user: User) -> DeviceComponentInstance:
        """
        특정 장치에서 부품 인스턴스를 연결 해제(삭제)합니다.
        """
        db_obj = device_component_instance_query_crud.get_by_device_id_and_supported_component_id(
            db, device_id=device_id, supported_component_id=supported_component_id, instance_name=instance_name
        )
        if not db_obj:
            raise NotFoundError(resource_name="DeviceComponentInstance", resource_id=f"device {device_id}, supported_component {supported_component_id}, and instance_name {instance_name}")
        
        deleted_value = db_obj.as_dict()
        
        deleted_instance = device_component_instance_command_crud.remove(db, id=db_obj.id)
        db.flush() # DB 세션에 변경사항 반영

        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="DeviceComponentInstance",
            resource_id=db_obj.id,
            deleted_value=deleted_value
        )
        return deleted_instance


device_component_instance_command_service = DeviceComponentInstanceCommandService()
