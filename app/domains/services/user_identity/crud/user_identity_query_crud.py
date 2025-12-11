from sqlalchemy.orm import Session
from typing import Optional

from app.core.crud_base import CRUDBase
from app.models.objects.user import User
from ..schemas.user_identity_command import UserCreate, UserUpdate # Even query CRUD needs these for the base class

class CRUDUserQuery(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

user_identity_query_crud = CRUDUserQuery(model=User)
