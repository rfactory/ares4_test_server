import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

# inter_domain Provider를 통해 장치-부품 연결 정보를 조회합니다.
from app.domains.inter_domain.device_component_management.device_component_query_provider import device_component_query_provider

logger = logging.getLogger(__name__)

class DeviceAttachmentValidator:
    def validate(
        self,
        db: Session,
        *,
        device_id: int,
        supported_component_id: int,
        instance_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        특정 부품 '인스턴스'가 장치에 연결되도록 사용자가 설정했는지 검증합니다.
        """
        # instance_name까지 사용하여 정확한 인스턴스를 조회합니다.
        component_instance = device_component_query_provider.get_instance_by_device_component_and_name(
            db, device_id=device_id, supported_component_id=supported_component_id, instance_name=instance_name
        )

        if not component_instance:
            msg = f"Component instance '{instance_name}' (Type ID: {supported_component_id}) is not attached to device (ID: {device_id})."
            logger.warning(f"VALIDATOR: {msg}")
            return False, msg

        return True, None

device_attachment_validator = DeviceAttachmentValidator()