from app.core.crud_base import CRUDBase
from app.models.relationships.user_device import UserDevice
from ..schemas.user_device import UserDeviceCreate
from sqlalchemy.orm import Session
from typing import Optional, List

class CRUDUserDeviceLink(CRUDBase[UserDevice, UserDeviceCreate, UserDevice]):
    def get_multi_by_device(self, db: Session, *, device_id: int) -> List[UserDevice]:
        return db.query(self.model).filter(self.model.device_id == device_id).all()

    def get_by_user_and_device_with_role(self, db: Session, *, user_id: int, device_id: int, role: str) -> Optional[UserDevice]:
        return db.query(self.model).filter(self.model.user_id == user_id, self.model.device_id == device_id, self.model.role == role).first()

    def get_links_by_user(self, db: Session, *, user_id: int, nicknames: Optional[List[str]] = None) -> List[UserDevice]:
        query = db.query(self.model).filter(self.model.user_id == user_id)
        if nicknames:
            query = query.filter(self.model.nickname.in_(nicknames))
        return query.all()

    def remove_by_user_and_device(self, db: Session, *, user_id: int, device_id: int) -> Optional[UserDevice]:
        obj = db.query(self.model).filter(self.model.user_id == user_id, self.model.device_id == device_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

user_device_link_crud = CRUDUserDeviceLink(UserDevice)
