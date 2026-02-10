import logging
from typing import Tuple, Optional
# 쿼리 결과로 넘어올 스키마 정보를 참조합니다.
from app.domains.inter_domain.device_management.schemas.device_query import DeviceRead

logger = logging.getLogger(__name__)

class DeviceExistenceValidator:
    """
    장치의 존재 여부 및 활성화 상태를 전문적으로 '판단'하는 Validator입니다.
    데이터 조회(Query)는 외부에서 수행된 후 결과값만 전달받습니다.
    """

    def validate_existence(self, *, device: Optional[DeviceRead]) -> Tuple[bool, Optional[str]]:
        """
        공급받은 장치 데이터를 바탕으로 접속 허용 여부를 판단합니다.
        
        - device: Query Provider가 조회한 결과물 (없으면 None)
        - 반환값: (성공여부, 에러메시지)
        """
        
        # 1. 존재 여부 판단 (데이터가 비어있는지 확인)
        if not device:
            return False, "Device existence check failed."

        # 2. 상태값 판단 (활성화된 기기인지 확인)
        # 나중에 'SUSPENDED', 'PENDING' 등 복잡한 상태 정책이 생겨도 여기서 관리합니다.
        if device.status != "ONLINE":
            msg = f"Device access denied: Current status is '{device.status}' (Expected: 'ONLINE')."
            logger.warning(f"[Validator] {msg} for ID: {device.id}")
            return False, msg

        # 모든 판단 통과
        logger.info(f"[Validator] Device existence and status verified for ID: {device.id}")
        return True, None

# 싱글톤 객체 생성
device_existence_validator = DeviceExistenceValidator()