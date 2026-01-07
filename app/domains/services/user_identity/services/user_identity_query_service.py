from sqlalchemy.orm import Session
from typing import Optional

from ..crud.user_identity_query_crud import user_identity_query_crud
from app.models.objects.user import User as DBUser

class UserIdentityQueryService:
    def get_user_by_id(self, db: Session, *, user_id: int) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_id(db, user_id=user_id)

    def get_user_by_username(self, db: Session, *, username: str) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_username(db, username=username)

    def get_user_by_email(self, db: Session, *, email: str) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_email(db, email=email)

    def get_user(self, db: Session, *, user_id: int) -> Optional[DBUser]:
        return user_identity_query_crud.get(db, id=user_id)

user_identity_query_service = UserIdentityQueryService()
