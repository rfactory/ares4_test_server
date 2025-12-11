# --- 조회 관련 CRUD ---
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.relationships.user_device import UserDevice

class CRUDUserDeviceLinkQuery:
    def get_by_user_id_and_device_id(
        self, db: Session, *, user_id: int, device_id: int
    ) -> Optional[UserDevice]:
        """사용자 ID와 기기 ID로 특정 사용자-기기 연결을 조회합니다."""
        return db.query(UserDevice).filter(
            UserDevice.user_id == user_id, UserDevice.device_id == device_id
        ).first()

    def get_all_for_user(self, db: Session, *, user_id: int) -> List[UserDevice]:
        """특정 사용자와 연결된 모든 기기 링크를 조회합니다."""
        return db.query(UserDevice).filter(UserDevice.user_id == user_id).all()

    def get_all_for_device(self, db: Session, *, device_id: int) -> List[UserDevice]:
        """특정 기기와 연결된 모든 사용자 링크를 조회합니다."""
        return db.query(UserDevice).filter(UserDevice.device_id == device_id).all()

user_device_link_query_crud = CRUDUserDeviceLinkQuery()
