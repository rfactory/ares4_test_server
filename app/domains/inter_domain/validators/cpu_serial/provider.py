# inter_domain/validators/cpu_serial/provider.py

from typing import Tuple, Optional, Dict # Dict는 payload 타입 힌팅에 필요

# Validator 임포트
from app.domains.action_authorization.validators.cpu_serial.validator import cpu_serial_validator
# 스키마 임포트 (Validator에게 넘겨줄 device 객체의 타입 힌팅용)
from app.domains.inter_domain.device_management.schemas.device_query import DeviceRead # Public DeviceRead 스키마

class CpuSerialValidatorProvider:
    """
    CpuSerialValidator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(
        self,
        *,
        device: DeviceRead,
        payload: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        주어진 장치 객체의 CPU 시리얼과 페이로드의 CPU 시리얼이 일치하는지 검증합니다.
        """
        return cpu_serial_validator.validate(
            device=device,
            payload=payload
        )

cpu_serial_validator_provider = CpuSerialValidatorProvider()
