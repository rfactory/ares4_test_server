# inter_domain/device_management/hmac_query_provider.py

from app.domains.services.device_management.services.hmac_query_service import hmac_query_service

class HmacQueryProvider:
    """
    HMAC 관련 조회/검증 서비스의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def verify_hmac(self, key_name: str, payload: str, signature: str) -> bool:
        """
        HMAC 서명을 검증합니다. 실제 로직은 서비스 계층에 위임됩니다.
        """
        return hmac_query_service.verify_hmac(
            key_name=key_name,
            payload=payload,
            signature=signature
        )

hmac_query_provider = HmacQueryProvider()
