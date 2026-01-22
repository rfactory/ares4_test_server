from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from typing import Optional

from app.models.objects.user import User
from app.models.objects.refresh_token import RefreshToken
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from app.domains.services.token_management.crud.token_management_command_crud import token_management_command_crud
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class TokenManagementCommandService:
    def issue_token_pair(self, db: Session, *, user: User, dpop_jkt: Optional[str] = None) -> dict:
        """
        주어진 사용자에 대해 Access Token과 Refresh Token 쌍을 발급하고 로그인 이벤트를 감사합니다.
        """
        # Access Token 생성
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_str = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires, dpop_jkt=dpop_jkt
        )

        # Refresh Token 생성 및 DB 저장
        refresh_token_expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_expires_at = datetime.now(timezone.utc) + refresh_token_expires_delta
        refresh_token_str = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires_delta
        )

        token_management_command_crud.create(
            db, 
            user_id=user.id, 
            token=refresh_token_str, 
            expires_at=refresh_token_expires_at
        )

        # 감사 로그: 사용자 로그인 이벤트 기록
        audit_command_provider.log(
            db=db, 
            event_type="AUDIT", 
            description=f"User '{user.username}' logged in successfully, issued token pair.",
            actor_user=user,
            target_user=user
        )

        return {"access_token": access_token_str, "refresh_token": refresh_token_str, "token_type": "bearer"}

    def rotate_token(self, db: Session, *, refresh_token_obj: RefreshToken, user: User, dpop_jkt: Optional[str] = None) -> dict:
        """
        이전 Refresh Token을 폐기하고 새로운 Access/Refresh Token 쌍을 발급합니다.
        """
        # 1. 이전 Refresh Token 폐기
        token_management_command_crud.revoke(db, refresh_token_obj=refresh_token_obj)

        # 2. 새로운 토큰 쌍 발급 (같은 클래스 내의 메소드 호출)
        new_token_pair = self.issue_token_pair(db, user=user, dpop_jkt=dpop_jkt)

        return new_token_pair

    def revoke_all_user_tokens(self, db: Session, *, user_id: int) -> int:
        """
        특정 사용자의 모든 Refresh Token을 폐기합니다.
        """
        return token_management_command_crud.revoke_all_for_user(db, user_id=user_id)

token_management_command_service = TokenManagementCommandService()
