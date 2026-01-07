from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.domains.services.user_identity.services.user_identity_command_service import user_identity_command_service
from app.models.objects.user import User
from app.domains.services.user_identity.schemas.user_identity_command import UserCreate, UserUpdate

class UserIdentityCommandProvider:
    async def create_user_and_log(self, db: Session, *, user_in: UserCreate, created_by: Optional[User] = None, is_active: bool = True) -> User:
        return await user_identity_command_service.create_user_and_log(db, user_in=user_in, created_by=created_by, is_active=is_active)

    def create_user_with_prehashed_password(self, db: Session, *, user_data: Dict[str, Any], is_active: bool = True) -> User:
        return user_identity_command_service.create_user_with_prehashed_password(db=db, user_data=user_data, is_active=is_active)

    def update_user(self, db: Session, *, user_id: int, user_in: UserUpdate, actor_user: User) -> User:
        return user_identity_command_service.update_user(db=db, user_id=user_id, user_in=user_in, actor_user=actor_user)

    def delete_user(self, db: Session, *, user_id: int, actor_user: User) -> User:
        return user_identity_command_service.delete_user(db=db, user_id=user_id, actor_user=actor_user)

    def activate_user(self, db: Session, *, user: User, actor_user: Optional[User]) -> User:
        return user_identity_command_service.activate_user(db=db, user=user, actor_user=actor_user)

user_identity_command_provider = UserIdentityCommandProvider()
