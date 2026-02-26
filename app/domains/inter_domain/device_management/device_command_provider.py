# inter_domain/device_management/device_command_provider.py
from sqlalchemy.orm import Session
from typing import Optional
from app.models.objects.device import Device as DBDevice
from app.domains.services.device_management.services.device_command_service import device_management_command_service, DeviceManagementCommandService
from app.domains.services.device_management.schemas.device_command import DeviceCreate, DeviceUpdate

class DeviceManagementCommandProvider:
    def get_service(self) -> DeviceManagementCommandService:
        """
        Policy 계층에서 서비스에 직접 접근할 수 있도록 인스턴스를 반환합니다.
        이 메서드가 추가되어야 Policy에서 흰색으로 나오지 않습니다.
        """
        return device_management_command_service
    def create_device(self, db: Session, *, obj_in: DeviceCreate, actor_user: Optional[any] = None) -> DBDevice:
        """새로운 장치 생성을 위한 안정적인 인터페이스를 제공합니다."""
        return device_management_command_service.create_device(db, obj_in=obj_in, actor_user=actor_user)

    def update_device(self, db: Session, *, device_id: int, obj_in: DeviceUpdate, actor_user: Optional[any] = None) -> DBDevice:
        """장치 정보 업데이트를 위한 안정적인 인터페이스를 제공합니다."""
        return device_management_command_service.update_device(
            db, device_id=device_id, obj_in=obj_in, actor_user=actor_user
        )

    def delete_device(self, db: Session, *, device_id: int, actor_user: Optional[any] = None) -> DBDevice:
        """장치 삭제를 위한 안정적인 인터페이스를 제공합니다."""
        return device_management_command_service.delete_device(db, device_id=device_id, actor_user=actor_user)
    
    def update_last_seen_at(self, db: Session, device_id: int):
        """[Inter-Domain] 기기 활동 시간 업데이트 인터페이스"""
        return device_management_command_service.update_last_seen(db, device_id=device_id)
    
    def assign_to_unit(self, db: Session, *, device_id: int, unit_id: int, role: str) -> DBDevice:
        return device_management_command_service.assign_to_unit(
            db, device_id=device_id, unit_id=unit_id, role=role
        )
        
    def unbind_device(self, db: Session, *, device_id: int) -> DBDevice:
        """기기를 유닛에서 해제하는 도메인 간 인터페이스"""
        return device_management_command_service.unbind_from_unit(
            db, device_id=device_id
        )
    
    def rotate_master(self, db: Session, *, unit_id: int, new_master_id: int) -> None:
        """[Inter-Domain] 마스터 권한 순환 명령 인터페이스"""
        return device_management_command_service.rotate_master(
            db, unit_id=unit_id, new_master_id=new_master_id
        )

device_management_command_provider = DeviceManagementCommandProvider()
