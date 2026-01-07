from sqlalchemy.orm import Session
from typing import Optional

from app.domains.services.user_identity.services.user_identity_query_service import user_identity_query_service
from .schemas.models import User # Re-export for inter-domain usage

class UserIdentityQueryProvider:
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return user_identity_query_service.get_user_by_id(db, user_id=user_id)

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return user_identity_query_service.get_user_by_username(db, username=username)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return user_identity_query_service.get_user_by_email(db, email=email)

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return user_identity_query_service.get_user(db, user_id=user_id)

user_identity_query_provider = UserIdentityQueryProvider()
