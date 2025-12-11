from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.core.utils import generate_random_code
from app.core.config import settings
from app.models.objects.user import User
from app.domains.services.user_2fa_state.crud import user_2fa_state_command_crud
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class User2faStateCommandService:
    """
    사용자의 2FA 상태를 관리하는 단일 책임을 갖는 서비스입니다.
    """
    def set_code(self, db: Session, *, user: User) -> str:
        """
        새로운 2FA 코드를 생성하여 DB에 저장하고, 생성된 코드를 반환합니다.
        """
        old_value = user.as_dict()
        
        code = generate_random_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
        
        updated_user = user_2fa_state_command_crud.set_2fa_code_in_db(
            db=db, user=user, code=code, expires_at=expires_at
        )
        # db.commit()     ← 삭제
        # db.refresh()    ← 삭제

        audit_command_provider.log_update(
            db=db,
            actor_user=user, # The user is performing the action on themselves
            resource_name="User2FAState",
            resource_id=user.id,
            old_value=old_value,
            new_value=updated_user.as_dict()
        )
        return code  # ← Policy에서 commit

    def clear_code(self, db: Session, *, user: User) -> None:
        """
        사용한 2FA 코드를 DB에서 삭제합니다.
        """
        old_value = user.as_dict()

        updated_user = user_2fa_state_command_crud.clear_2fa_code_in_db(db=db, user=user)
        # db.commit()     ← 삭제
        # db.refresh()    ← 삭제

        audit_command_provider.log_update(
            db=db,
            actor_user=user,
            resource_name="User2FAState",
            resource_id=user.id,
            old_value=old_value,
            new_value=updated_user.as_dict()
        )
        # return None은 필요 없음

user_2fa_state_command_service = User2faStateCommandService()
