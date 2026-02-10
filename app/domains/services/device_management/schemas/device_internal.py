from typing import Optional
from pydantic import Field
from .device_query import DeviceRead 

class DeviceWithSecret(DeviceRead):
    """
    내부 서비스 및 보안 검증용으로 사용되는 장치 스키마.
    DB의 hmac_secret_key 필드를 포함하여 검증기에서 직접 계산할 수 있도록 합니다.
    """
    cpu_serial: str = Field(..., description="장치의 CPU 고유 시리얼 번호")
    
    # 기존 Vault 연동용 필드 (하위 호환성을 위해 유지)
    hmac_key_name: Optional[str] = Field(None, description="Vault에 저장된 HMAC 키의 이름")
    
    # [핵심 추가] DB에 저장된 실제 시크릿 키를 담는 필드
    hmac_secret_key: Optional[str] = Field(None, description="DB에 저장된 개별 장치 고유 HMAC 비밀키")