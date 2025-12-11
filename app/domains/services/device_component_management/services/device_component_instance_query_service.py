# services/device_component_instance_query_service.py

from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.device_component_instance_query_crud import device_component_instance_query_crud
from ..schemas.device_component_instance_query import DeviceComponentInstanceRead
from app.models.relationships.device_component_instance import DeviceComponentInstance

class DeviceComponentInstanceQueryService:
    """장치-부품 연결 인스턴스 조회 관련 서비스를 담당합니다."""

    def get_components_for_device(self, db: Session, *, device_id: int) -> List[DeviceComponentInstanceRead]:
        """특정 장치에 연결된 모든 부품 인스턴스 목록을 조회합니다."""
        instances = device_component_instance_query_crud.get_instances_by_device_id(db, device_id=device_id)
        return [DeviceComponentInstanceRead.from_orm(instance) for instance in instances]

    def get_instance_by_device_component_and_name(
        self, db: Session, *, device_id: int, supported_component_id: int, instance_name: str
    ) -> Optional[DeviceComponentInstance]:
        """특정 장치, 부품 ID, 인스턴스 이름으로 단일 연결 인스턴스를 조회합니다."""
        return device_component_instance_query_crud.get_by_device_id_and_supported_component_id(
            db, device_id=device_id, supported_component_id=supported_component_id, instance_name=instance_name
        )

device_component_instance_query_service = DeviceComponentInstanceQueryService()
