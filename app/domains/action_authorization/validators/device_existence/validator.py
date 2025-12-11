import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional
from uuid import UUID

# inter_domain의 올바른 경로에서 provider와 schema를 가져옵니다.
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider

logger = logging.getLogger(__name__)

class DeviceExistenceValidator:
    def validate(self, db: Session, *, device_uuid_str: str) -> Tuple[bool, Optional[str]]:
        """
        주어진 UUID로 장치가 DB에 실제로 존재하는지 확인하는 '판단'을 내립니다.
        성공 시 (True, None), 실패 시 (False, "에러 메시지")를 반환합니다.
        """
        try:
            device_uuid = UUID(device_uuid_str)
        except ValueError:
            return False, f"Invalid device UUID format: {device_uuid_str}"

        # get_device_by_uuid를 사용하여 장치를 직접 조회합니다.
        device = device_management_query_provider.get_device_by_uuid(db, current_uuid=device_uuid)
        
        if not device:
            msg = f"Device with UUID {device_uuid_str} not found."
            logger.warning(f"VALIDATOR: {msg}")
            return False, msg
        
        # 장치가 존재하므로 검증 성공
        return True, None

device_existence_validator = DeviceExistenceValidator()