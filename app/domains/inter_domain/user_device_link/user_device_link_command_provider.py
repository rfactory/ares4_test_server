# --- 사용자-기기 연결 명령 Provider ---
from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User
from app.models.relationships.user_device import UserDevice
from app.domains.services.user_device_link.schemas.user_device_link_command import UserDeviceLinkCreate, UserDeviceLinkUpdate
from app.domains.services.user_device_link.services.user_device_link_command_service import user_device_link_command_service

class UserDeviceLinkCommandProvider:
    def link_device_to_user(
        self,
        db: Session,
        *,
        link_in: UserDeviceLinkCreate,
        actor_user: User,
    ) -> UserDevice:
        """
        사용자와 기기 간의 링크를 생성하는 안정적인 인터페이스를 제공합니다.
        Policy 계층에서 호출될 것을 예상합니다.
        """
        return user_device_link_command_service.link_device_to_user(
            db=db,
            link_in=link_in,
            actor_user=actor_user
        )

    def update_link(
        self,
        db: Session,
        *,
        user_id: int,
        device_id: int,
        link_in: UserDeviceLinkUpdate,
        actor_user: User,
    ) -> Optional[UserDevice]:
        """
        사용자와 기기 간의 기존 링크를 업데이트하는 안정적인 인터페이스를 제공합니다.
        """
        return user_device_link_command_service.update_link(
            db=db,
            user_id=user_id,
            device_id=device_id,
            link_in=link_in,
            actor_user=actor_user
        )

    def remove_link(
        self,
        db: Session,
        *,
        user_id: int,
        device_id: int,
        actor_user: User,
    ) -> None:
        """
        사용자와 기기 간의 링크를 삭제하는 안정적인 인터페이스를 제공합니다.
        """
        return user_device_link_command_service.remove_link(
            db=db,
            user_id=user_id,
            device_id=device_id,
            actor_user=actor_user
        )

user_device_link_command_provider = UserDeviceLinkCommandProvider()
