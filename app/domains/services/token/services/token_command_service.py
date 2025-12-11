from datetime import timedelta

from sqlalchemy.orm import Session # Session 임포트

from app.core.security import create_access_token
from app.core.config import settings
from app.models.objects.user import User
from app.domains.services.token.schemas.token_command import Token
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class TokenCommandService:
    """
    JWT 접근 토큰을 발급하는 단일 책임을 갖는 서비스입니다.
    """
    def issue_token(self, db: Session, *, user: User) -> Token: # db: Session 인자 추가
        """
        주어진 사용자에 대해 새로운 JWT 접근 토큰을 생성하고, 로그인 이벤트를 감사합니다.
        이 메소드는 상위 Policy 계층에서 호출되며, 동일한 DB 트랜잭션 내에서 처리됩니다.
        """
        # 감사 로그: 사용자 로그인 이벤트 기록 (동일 트랜잭션 내에서 처리)
        audit_command_provider.log_creation(
            db=db, # Policy에서 넘겨받은 DB 세션 사용
            actor_user=user,
            resource_name="UserLogin",
            resource_id=user.id,
            new_value={"status": "success", "user_id": user.id, "username": user.username, "email": user.email}
        )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_str = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token_str, token_type="bearer")

token_command_service = TokenCommandService()
