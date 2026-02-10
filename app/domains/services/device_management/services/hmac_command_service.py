# services/device_management/services/hmac_command_service.py

from ..repositories.vault_hmac_repository import vault_hmac_repository

class HmacCommandService:
    """
    HMAC 키 생성(쓰기) 관련 기능을 제공하는 서비스입니다.
    실제 로직은 VaultHmacRepository에 위임합니다.
    """
    def create_hmac_key(self, device_id: str) -> str:
        return vault_hmac_repository.create_hmac_key(device_id=device_id)
    
    def store_device_hmac(self, path: str, key: str):
        """
        [추가] Policy 계층의 요구사항에 따라 
        특정 경로(Vault path)에 생성된 HMAC 키를 명시적으로 저장합니다.
        """
        return vault_hmac_repository.store_hmac(path=path, key=key)

hmac_command_service = HmacCommandService()
