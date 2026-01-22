from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User
from app.models.objects.refresh_token import RefreshToken
from app.domains.services.token_management.services.token_management_command_service import token_management_command_service

class TokenManagementCommandProvider:
    def issue_token_pair(self, db: Session, *, user: User, dpop_jkt: Optional[str] = None) -> dict:
        """Access Token과 Refresh Token 쌍을 발급하고 DB에 저장합니다."""
        return token_management_command_service.issue_token_pair(db=db, user=user, dpop_jkt=dpop_jkt)

    def rotate_token(self, db: Session, *, refresh_token_obj: RefreshToken, user: User, dpop_jkt: Optional[str] = None) -> dict:
        """이전 Refresh Token을 폐기하고 새로운 토큰 쌍을 발급합니다."""
        return token_management_command_service.rotate_token(db=db, refresh_token_obj=refresh_token_obj, user=user, dpop_jkt=dpop_jkt)

    def revoke_all_user_tokens(self, db: Session, *, user_id: int) -> int:
        """특정 사용자의 모든 Refresh Token을 폐기합니다."""
        return token_management_command_service.revoke_all_user_tokens(db=db, user_id=user_id)

token_management_command_provider = TokenManagementCommandProvider()
