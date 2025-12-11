# schemas/user_settings_command.py
from pydantic import BaseModel
from typing import Optional

# 현재 toggle_2fa는 복잡한 입력 스키마를 요구하지 않지만,
# 도메인의 명령 스키마 구조를 유지하기 위한 플레이스홀더입니다.
class UserSettingsToggle2FA(BaseModel):
    # 2FA 상태를 직접 지정할 필요 없이, 토글 작업은 현재 상태를 반전시키므로
    # 입력 필드는 비워둡니다. 향후 특정 상태로 설정하는 기능이 추가될 수 있습니다.
    pass

class UserSettingsUpdate(BaseModel):
    # 향후 다른 설정 항목이 추가될 경우를 대비한 스키마
    pass
