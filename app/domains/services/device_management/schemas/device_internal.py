# schemas/device_internal.py
from typing import Optional
from pydantic import Field

from .device_query import DeviceRead # 기본 스키마를 import

class DeviceWithSecret(DeviceRead):
    """
    내부 서비스 및 보안 검증용으로 사용되는 장치 스키마.
    shared_secret과 같이 민감한 정보를 포함합니다.
    """
    cpu_serial: str = Field(..., description="장치의 CPU 고유 시리얼 번호")
    hmac_key_name: Optional[str] = Field(None, description="Vault에 저장된 HMAC 키의 이름")

    # model_config은 DeviceRead에서 상속받으므로 다시 정의할 필요 없음
