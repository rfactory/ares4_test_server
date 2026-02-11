# inter_domain/device_management/device_internal_query_provider.py

from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.domains.services.device_management.services.device_query_service import device_management_query_service
from app.domains.services.device_management.schemas.device_internal import DeviceWithSecret # 새로 만든 스키마 임포트

class DeviceInternalQueryProvider:
    """
    내부 보안 검증과 같이 특수한 목적으로, 민감한 정보를 포함한 장치 정보를 제공하는 Provider입니다.
    """
    def get_device_with_secret_by_uuid(self, db: Session, *, current_uuid: UUID) -> Optional[DeviceWithSecret]:
        """
        UUID로 장치 정보를 조회하며, shared_secret과 같은 민감한 정보를 포함합니다.
        """
        # 서비스 계층에서는 DB 모델을 반환하므로, 이를 DeviceWithSecret 스키마로 변환합니다.
        db_device = device_management_query_service.get_device_model_by_uuid(db, current_uuid=current_uuid)
        
        if not db_device: return None
        
        # DB 모델 객체를 DeviceWithSecret 스키마로 변환
        return DeviceWithSecret.model_validate(db_device)

device_internal_query_provider = DeviceInternalQueryProvider()
