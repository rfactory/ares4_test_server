# inter_domain/device_management/hmac_command_provider.py

from app.domains.services.device_management.services.hmac_command_service import hmac_command_service, HmacCommandService

class HmacCommandProvider:
    """
    HMAC 키 생성(쓰기) 관련 서비스의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def get_service(self) -> HmacCommandService:
        return hmac_command_service
    
    def create_hmac_key(self, device_id: str) -> str:
        return hmac_command_service.create_hmac_key(device_id=device_id)

hmac_command_provider = HmacCommandProvider()
