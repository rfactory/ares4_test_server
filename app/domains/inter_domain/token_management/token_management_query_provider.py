from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.refresh_token import RefreshToken
from app.domains.services.token_management.services.token_management_query_service import token_management_query_service
from app.core.schemas.token import TokenPayload

class TokenManagementQueryProvider:
    def get_refresh_token_obj(self, db: Session, *, token: str) -> Optional[RefreshToken]:
        """문자열 토큰으로 RefreshToken 객체를 조회합니다."""
        return token_management_query_service.get_refresh_token_obj(db=db, token=token)

    def get_token_payload(self, *, token: str) -> TokenPayload:
        """JWT 토큰의 payload를 디코딩하여 반환합니다."""
        return token_management_query_service.get_token_payload(token=token)

token_management_query_provider = TokenManagementQueryProvider()
