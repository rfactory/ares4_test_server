# --- 조회 관련 스키마 ---
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 순환 참조를 피하기 위한 중첩 객체 기본 스키마
# 실제 시나리오에서는 각 도메인에서 임포트될 수 있습니다.
class UserRead(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class DeviceRead(BaseModel):
    id: int
    cpu_serial: str
    current_uuid: str

    class Config:
        from_attributes = True

class UserDeviceLinkRead(BaseModel):
    id: int
    user_id: int
    device_id: int
    role: str
    nickname: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    user: UserRead
    device: DeviceRead

    class Config:
        from_attributes = True
