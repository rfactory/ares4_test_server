from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User
from app.domains.accounts.schemas import UserCreate
from app.core.security import get_password_hash
from app.core.exceptions import DuplicateEntryError, NotFoundError

class CRUDUser:
    def get_user_by_username(self, db: Session, username: str) -> User:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise NotFoundError(resource_name="User", resource_id=username)
        return user

    def get_user_by_email(self, db: Session, email: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise NotFoundError(resource_name="User", resource_id=email)
        return user

    def register_new_user(self, db: Session, *, user_in: UserCreate) -> User:
        """
        Handles public user self-registration.
        - No permission checks are performed.
        - Checks for duplicate username and email.
        """
        if db.query(User).filter(User.username == user_in.username).first():
            raise DuplicateEntryError("User", "username", user_in.username)

        if db.query(User).filter(User.email == user_in.email).first():
            raise DuplicateEntryError("User", "email", user_in.email)

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            password_hash=hashed_password,
            is_active=True,  # Users are active by default, may require email verification later
            is_staff=False,   # Never assign staff/superuser status on public registration
            is_superuser=False,
            is_two_factor_enabled=user_in.is_two_factor_enabled
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

user_crud = CRUDUser()
