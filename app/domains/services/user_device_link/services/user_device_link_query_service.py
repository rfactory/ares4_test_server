# --- 조회 관련 서비스 ---
# 이 파일은 사용자와 기기 연결 상태를 조회하는 서비스를 제공합니다.

from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.relationships.user_device import UserDevice
from ..crud.user_device_link_query_crud import user_device_link_query_crud
from ..schemas.user_device_link_query import UserDeviceLinkRead

class UserDeviceLinkQueryService:
    def get_link_by_user_and_device(
        self, db: Session, *, user_id: int, device_id: int
    ) -> Optional[UserDeviceLinkRead]:
        """사용자 ID와 기기 ID로 특정 사용자-기기 연결을 조회합니다."""
        db_obj = user_device_link_query_crud.get_by_user_id_and_device_id(db, user_id=user_id, device_id=device_id)
        return UserDeviceLinkRead.model_validate(db_obj) if db_obj else None

    def get_all_links_for_user(self, db: Session, *, user_id: int) -> List[UserDeviceLinkRead]:
        """특정 사용자와 연결된 모든 기기 링크를 조회합니다."""
        db_objs = user_device_link_query_crud.get_all_for_user(db, user_id=user_id)
        return [UserDeviceLinkRead.model_validate(obj) for obj in db_objs]

    def get_all_links_for_device(self, db: Session, *, device_id: int) -> List[UserDeviceLinkRead]:
        """특정 기기와 연결된 모든 사용자 링크를 조회합니다."""
        db_objs = user_device_link_query_crud.get_all_for_device(db, device_id=device_id)
        return [UserDeviceLinkRead.model_validate(obj) for obj in db_objs]

user_device_link_query_service = UserDeviceLinkQueryService()
