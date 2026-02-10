# inter_domain/device_management/device_command_provider.py
from sqlalchemy.orm import Session

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
    def create_device(self, db: Session, *, obj_in: DeviceCreate) -> DBDevice:
        """새로운 장치 생성을 위한 안정적인 인터페이스를 제공합니다."""
        return device_management_command_service.create_device(db, obj_in=obj_in)

    def update_device(self, db: Session, *, device_id: int, obj_in: DeviceUpdate) -> DBDevice:
        """장치 정보 업데이트를 위한 안정적인 인터페이스를 제공합니다."""
        return device_management_command_service.update_device(db, device_id=device_id, obj_in=obj_in)

    def delete_device(self, db: Session, *, device_id: int) -> DBDevice:
        """장치 삭제를 위한 안정적인 인터페이스를 제공합니다."""
        return device_management_command_service.delete_device(db, device_id=device_id)

device_management_command_provider = DeviceManagementCommandProvider()
