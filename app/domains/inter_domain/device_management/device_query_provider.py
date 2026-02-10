# inter_domain/device_management/device_query_provider.py
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID # UUID 타입 힌팅을 위해 추가

from app.domains.services.device_management.services.device_query_service import device_management_query_service
from app.domains.services.device_management.schemas.device_query import DeviceQuery, DeviceRead

class DeviceManagementQueryProvider:
    def get_devices(self, db: Session, *, query_params: DeviceQuery) -> List[DeviceRead]:
        """장치 목록을 조회하는 안정적인 인터페이스를 제공합니다."""
        return device_management_query_service.get_devices(db, query_params=query_params)

    def get_device_by_id(self, db: Session, *, id: int) -> Optional[DeviceRead]:
        """ID로 단일 장치를 조회하는 안정적인 인터페이스를 제공합니다."""
        return device_management_query_service.get_device_by_id(db, id=id)

    def get_device_by_uuid(self, db: Session, *, current_uuid: UUID) -> Optional[DeviceRead]:
        """UUID로 단일 장치를 조회하는 안정적인 인터페이스를 제공합니다."""
        return device_management_query_service.get_device_by_uuid(db, current_uuid=current_uuid)
    
    def get_service(self):
        """
        Policy 계층에서 서비스를 가져올 때 사용합니다.
        이제 VS Code에서 이 메서드를 인식하여 하위 메서드(get_by_serial 등)를 추천해줍니다.
        """
        return device_management_query_service
    
    def get_device_by_identifier(self, db: Session, *, identifier: str) -> Optional[DeviceRead]:
        """
        UUID 또는 CPU Serial을 통해 장치 정보를 조회합니다.
        CRUD 단계에서 joinedload가 적용되어 소유권(Org, User) 정보가 포함된 DeviceRead를 반환합니다.
        """
        return device_management_query_service.get_device_by_identifier(db, identifier=identifier)

device_management_query_provider = DeviceManagementQueryProvider()
