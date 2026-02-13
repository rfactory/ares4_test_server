from sqlalchemy.orm import Session
from typing import Optional
from app.models.objects.provisioning_token import ProvisioningToken
from app.domains.services.provisioning_token.services.provisioning_token_query_service import provisioning_token_query_service

class ProvisioningTokenQueryProvider:
    """
    [Inter-Domain Provider] 
    프로비저닝 토큰 도메인의 조회 기능을 외부(Policy 등)에 제공합니다.
    """

    def get_by_value(self, db: Session, token_value: str) -> Optional[ProvisioningToken]:
        """
        토큰 문자열을 기반으로 정보를 조회합니다.
        (Query Service의 get_token_by_value를 호출합니다.)
        """
        return provisioning_token_query_service.get_token_by_value(db, token_value)

# 싱글톤 인스턴스
provisioning_token_query_provider = ProvisioningTokenQueryProvider()