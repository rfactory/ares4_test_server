# schemas/user_settings_query.py
from pydantic import BaseModel, ConfigDict

# 사용자 설정 조회 시 반환될 스키마
# UserSettings 모델이 아직 없으므로 User 모델의 일부 필드를 가정
class UserSettingsRead(BaseModel):
    is_two_factor_enabled: bool

    model_config = ConfigDict(from_attributes=True)
