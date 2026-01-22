from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.refresh_token import RefreshToken
from app.domains.services.token_management.crud.token_management_query_crud import token_management_query_crud
from app.core.security import verify_access_token
from app.core.schemas.token import TokenPayload # 수정된 경로

class TokenManagementQueryService:
    def get_refresh_token_obj(self, db: Session, *, token: str) -> Optional[RefreshToken]:
        """문자열 토큰으로 RefreshToken 객체를 조회합니다."""
        return token_management_query_crud.get_by_token(db=db, token=token)
    
    def get_token_payload(self, *, token: str) -> TokenPayload:
        """JWT 토큰의 payload를 디코딩하여 반환합니다."""
        token_data = verify_access_token(token)
        return TokenPayload(id=token_data.id)

token_management_query_service = TokenManagementQueryService()
