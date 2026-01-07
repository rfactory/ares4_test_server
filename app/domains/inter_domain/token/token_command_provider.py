from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.services.token.services.token_command_service import token_command_service
from app.domains.services.token.schemas.token_command import Token

class TokenCommandProvider:
    """
    token_command_service의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def issue_token(self, db: Session, *, user: User) -> Token:
        """
        내부 token_command_service를 호출하여 토큰을 발급합니다.
        """
        return token_command_service.issue_token(db=db, user=user)


token_command_provider = TokenCommandProvider()

