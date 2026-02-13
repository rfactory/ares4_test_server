from sqlalchemy.orm import Session
from typing import Optional
from app.models.objects.provisioning_token import ProvisioningToken

class ProvisioningTokenQueryCRUD:
    def get_by_value(self, db: Session, token_value: str) -> Optional[ProvisioningToken]:
        """
        토큰 값으로 ProvisioningToken 객체를 조회합니다.
        유효성 검사(만료, 사용 여부 등)는 Validator에서 수행합니다.
        """
        return db.query(ProvisioningToken).filter(
            ProvisioningToken.token_value == token_value
        ).first()

# 싱글톤 인스턴스
provisioning_token_query_crud = ProvisioningTokenQueryCRUD()