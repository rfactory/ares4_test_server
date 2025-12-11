from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.crud_base import CRUDBase
from app.models.objects.user import User
from ..schemas.user_identity_command import UserCreate, UserUpdate

class CRUDUserCommand(CRUDBase[User, UserCreate, UserUpdate]):
    def create_with_hashed_password(self, db: Session, *, create_data: Dict[str, Any]) -> User:
        """사전에 해시된 비밀번호로 사용자를 생성합니다. 커밋은 수행하지 않습니다."""
        db_obj = User(**create_data)
        db.add(db_obj)
        db.flush() # ID 생성을 위해 flush 하지만, 커밋은 하지 않음
        return db_obj

    def remove(self, db: Session, *, id: int) -> User:
        """기본 remove 메소드를 오버라이드하여 soft delete를 구현합니다."""
        obj = db.query(self.model).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
        return obj

user_identity_command_crud = CRUDUserCommand(model=User)
