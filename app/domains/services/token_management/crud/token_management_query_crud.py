from sqlalchemy.orm import Session
from typing import Optional

from app.core.crud_base import CRUDBase
from app.models.objects.refresh_token import RefreshToken

class CRUDTokenManagementQuery(CRUDBase[RefreshToken, RefreshToken, RefreshToken]): 
    def get_by_token(self, db: Session, *, token: str) -> Optional[RefreshToken]:
        """폐기되지 않은 유효한 Refresh Token을 문자열을 기준으로 조회합니다."""
        return db.query(self.model).filter(self.model.token == token, self.model.is_revoked == False).first()

token_management_query_crud = CRUDTokenManagementQuery(RefreshToken)
