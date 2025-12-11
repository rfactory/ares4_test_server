from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.domains.services.user_2fa_state.services.user_2fa_state_command_service import user_2fa_state_command_service


class User2faStateCommandProvider:
    """
    user_2fa_state_command_service의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def set_code(self, db: Session, *, user: User) -> str:
        """
        내부 서비스를 호출하여 2FA 코드를 설정합니다.
        """
        return user_2fa_state_command_service.set_code(db=db, user=user)

    def clear_code(self, db: Session, *, user: User) -> None:
        """
        내부 서비스를 호출하여 2FA 코드를 삭제합니다.
        """
        user_2fa_state_command_service.clear_code(db=db, user=user)


user_2fa_state_command_provider = User2faStateCommandProvider()
