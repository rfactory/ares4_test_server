# --- 명령 관련 CRUD ---
from sqlalchemy.orm import Session

from app.core.crud_base import CRUDBase
from app.models.relationships.user_device import UserDevice
from ..schemas.user_device_link_command import UserDeviceLinkCreate, UserDeviceLinkUpdate

class CRUDUserDeviceLinkCommand(CRUDBase[UserDevice, UserDeviceLinkCreate, UserDeviceLinkUpdate]):
    # CRUDBase를 상속받아 기본적인 생성, 조회, 수정, 삭제 기능을 제공합니다.
    # UserDeviceLinkUpdate 스키마를 사용하여 업데이트를 처리합니다.
    pass

user_device_link_command_crud = CRUDUserDeviceLinkCommand(UserDevice)