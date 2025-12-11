# inter_domain/device_component_management/device_component_query_provider.py

from sqlalchemy.orm import Session
from typing import List, Optional # Optional 추가

from app.domains.services.device_component_management.services.device_component_instance_query_service import device_component_instance_query_service
from app.domains.services.device_component_management.schemas.device_component_instance_query import DeviceComponentInstanceRead
from app.models.relationships.device_component_instance import DeviceComponentInstance # DeviceComponentInstance 모델 임포트

class DeviceComponentQueryProvider:
    """
    장치-부품 연결 관련 Query 서비스의 기능을 외부 도메인에 노출하는 제공자입니다。
    """
    def get_components_for_device(self, db: Session, *, device_id: int) -> List[DeviceComponentInstanceRead]:
        return device_component_instance_query_service.get_components_for_device(db=db, device_id=device_id)

    def get_instance_by_device_component_and_name(
        self, db: Session, *, device_id: int, supported_component_id: int, instance_name: str
    ) -> Optional[DeviceComponentInstanceRead]: # 반환 타입을 Pydantic 스키마로 변경
        """특정 장치, 부품 ID, 인스턴스 이름으로 단일 연결 인스턴스를 조회합니다."""
        component_instance_model = device_component_instance_query_service.get_instance_by_device_component_and_name(
            db, device_id=device_id, supported_component_id=supported_component_id, instance_name=instance_name
        )
        if not component_instance_model:
            return None
        
        return DeviceComponentInstanceRead.model_validate(component_instance_model)

device_component_query_provider = DeviceComponentQueryProvider()
