# inter_domain/device_component_management/device_component_query_provider.py

from sqlalchemy.orm import Session
from typing import List, Optional # Optional 추가

from app.domains.services.device_component_management.services.device_component_instance_query_service import device_component_instance_query_service
from app.domains.services.device_component_management.schemas.device_component_instance_query import DeviceComponentInstanceRead
from app.models.relationships.device_component_instance import DeviceComponentInstance # DeviceComponentInstance 모델 임포트

class DeviceComponentQueryProvider:
    def get_components_for_device(self, db: Session, *, device_id: int) -> List[DeviceComponentInstanceRead]:
        # [수정] DB 모델 리스트를 받아서 Pydantic 리스트로 변환합니다.
        db_instances = device_component_instance_query_service.get_components_for_device(db=db, device_id=device_id)
        return [DeviceComponentInstanceRead.model_validate(inst) for inst in db_instances]

    def get_instance_by_device_component_and_name(
        self, db: Session, *, device_id: int, supported_component_id: int, instance_name: str
    ) -> Optional[DeviceComponentInstanceRead]:
        # [주의] import된 이름인 'device_component_instance_query_service'를 사용해야 합니다.
        model = device_component_instance_query_service.get_instance_by_device_component_and_name(
            db, device_id=device_id, supported_component_id=supported_component_id, instance_name=instance_name
        )
        
        if not model:
            return None
        
        return DeviceComponentInstanceRead.model_validate(model)

device_component_query_provider = DeviceComponentQueryProvider()