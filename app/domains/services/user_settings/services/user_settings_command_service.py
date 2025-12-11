from sqlalchemy.orm import Session
from app.models.objects.user import User as DBUser
from app.core.exceptions import NotFoundError
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider # 수정된 audit provider
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider # 수정된 user_identity query provider

class UserSettingsCommandService:
    """사용자 계정의 개별 설정을 관리하는 Command 서비스입니다."""
    def toggle_2fa(self, db: Session, *, current_user: DBUser) -> DBUser:
        """
        현재 사용자의 2단계 인증(2FA) 설정을 켜거나 끕니다.
        """
        # user_identity_providers를 통해 사용자 정보를 조회하는 대신,
        # 이미 인증된 current_user 객체를 직접 사용합니다.
        # (Policy 계층에서 current_user를 이미 가져왔다고 가정)
        
        # 현재 current_user 객체가 최신 상태임을 보장하기 위해 DB에서 다시 조회
        user_in_db = user_identity_query_provider.get_user(db, user_id=current_user.id)
        if not user_in_db:
            raise NotFoundError(resource_name="User", resource_id=str(current_user.id))

        old_value = user_in_db.as_dict() # 감사 로그를 위한 이전 상태 기록
        user_in_db.is_two_factor_enabled = not user_in_db.is_two_factor_enabled
        db.add(user_in_db)
        db.flush() # 변경 사항을 DB에 반영하고 ID 생성 보장

        # 감사 로그 기록 (상태 변경이므로 log_update 사용)
        audit_command_provider.log_update(
            db=db,
            actor_user=current_user,
            resource_name="User Setting (2FA)",
            resource_id=user_in_db.id,
            old_value=old_value,
            new_value=user_in_db.as_dict()
        )

        return user_in_db

user_settings_command_service = UserSettingsCommandService()