import logging
from typing import Tuple, Optional, Dict

# inter_domain에 새로 생성된 schemas 파일을 통해 스키마를 가져옵니다.
from app.domains.inter_domain.device_management.schemas.device_query import DeviceRead

logger = logging.getLogger(__name__)

class CpuSerialValidator:
    def validate(self, *, device: DeviceRead, payload: Dict) -> Tuple[bool, Optional[str]]:
        """
        주어진 장치 객체의 CPU 시리얼과 페이로드의 CPU 시리얼이 일치하는지 확인합니다.
        이는 SD 카드 스왑 공격 등을 방지하기 위한 보안 검증입니다.
        """
        payload_cpu_serial = payload.get('cpu_serial')
        if not payload_cpu_serial or payload_cpu_serial != device.cpu_serial:
            error_msg = (
                f"SECURITY_ALERT: CPU Serial mismatch for device UUID {device.current_uuid}! "
                f"DB expects '{device.cpu_serial}' but payload reported '{payload_cpu_serial}'. "
                f"Possible SD card swap attack."
            )
            logger.critical(error_msg)
            return False, error_msg
        
        return True, None

cpu_serial_validator = CpuSerialValidator()