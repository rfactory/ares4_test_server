from sqlalchemy.orm import Session
from app.models.objects.user import User as DBUser
from app.domains.services.user_settings.services.user_settings_command_service import user_settings_command_service

class UserSettingsCommandProvider:
    def toggle_2fa(self, db: Session, *, current_user: DBUser) -> DBUser:
        return user_settings_command_service.toggle_2fa(db=db, current_user=current_user)

user_settings_command_provider = UserSettingsCommandProvider()
