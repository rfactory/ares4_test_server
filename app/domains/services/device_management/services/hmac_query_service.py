# services/device_management/services/hmac_query_service.py

from ..repositories.vault_hmac_repository import vault_hmac_repository

class HmacQueryService:
    """
    HMAC 관련 조회/검증 기능을 제공하는 서비스입니다.
    실제 로직은 VaultHmacRepository에 위임합니다.
    """
    def verify_hmac(self, key_name: str, payload: str, signature: str) -> bool:
        return vault_hmac_repository.verify_hmac(
            key_name=key_name,
            payload=payload,
            signature=signature
        )

hmac_query_service = HmacQueryService()
