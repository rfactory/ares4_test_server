# --- 사용자-기기 연결 조회 Provider ---
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.relationships.user_device import UserDevice
from app.domains.services.user_device_link.schemas.user_device_link_query import UserDeviceLinkRead
from app.domains.services.user_device_link.services.user_device_link_query_service import user_device_link_query_service

class UserDeviceLinkQueryProvider:
    def get_link_by_user_and_device(
        self, db: Session, *, user_id: int, device_id: int
    ) -> Optional[UserDeviceLinkRead]:
        """사용자 ID와 기기 ID로 특정 사용자-기기 연결을 조회하는 안정적인 인터페이스를 제공합니다."""
        return user_device_link_query_service.get_link_by_user_and_device(db=db, user_id=user_id, device_id=device_id)

    def get_all_links_for_user(self, db: Session, *, user_id: int) -> List[UserDeviceLinkRead]:
        """특정 사용자와 연결된 모든 기기 링크를 조회하는 안정적인 인터페이스를 제공합니다."""
        return user_device_link_query_service.get_all_links_for_user(db=db, user_id=user_id)

    def get_all_links_for_device(self, db: Session, *, device_id: int) -> List[UserDeviceLinkRead]:
        """특정 기기와 연결된 모든 사용자 링크를 조회하는 안정적인 인터페이스를 제공합니다."""
        return user_device_link_query_service.get_all_links_for_device(db=db, device_id=device_id)

user_device_link_query_provider = UserDeviceLinkQueryProvider()
