from sqlalchemy.orm import Session
from typing import Optional
from app.models.objects.provisioning_token import ProvisioningToken
from app.domains.services.provisioning_token.crud.provisioning_token_query_crud import provisioning_token_query_crud

class ProvisioningTokenQueryService:
    """
    [Query Service] 프로비저닝 토큰(입장권) 정보 조회를 담당하는 서비스입니다.
    데이터의 유재성 확인 및 조회를 수행하며, 비즈니스 검증(Validator)을 위한 기초 데이터를 제공합니다.
    """

    def get_token_by_value(self, db: Session, token_value: str) -> Optional[ProvisioningToken]:
        """
        토큰 문자열을 기반으로 DB에서 ProvisioningToken 객체를 조회합니다.
        """
        return provisioning_token_query_crud.get_by_value(db, token_value)

# 싱글톤 인스턴스
provisioning_token_query_service = ProvisioningTokenQueryService()