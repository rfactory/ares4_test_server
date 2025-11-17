from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.users.schemas import UserCreate

class CRUDUser:
    def get_user_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, user: UserCreate):
        # Circular import fix: import get_password_hash inside the function
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=hashed_password,
            is_active=True,
            is_staff=False,
            is_superuser=False,
            is_two_factor_enabled=user.is_two_factor_enabled # is_two_factor_enabled 필드 추가
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

user_crud = CRUDUser()
