from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import SessionLocal
from app.core import security
# Correcting the import path from .users to .accounts
from app.domains.accounts import crud as user_crud
from app.models.objects.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    """
    현재 사용자를 가져옵니다.
    """
    try:
        # security.verify_access_token returns a TokenData object
        token_data = security.verify_access_token(token)
        if token_data is None or token_data.username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials, token data is invalid",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    # Using the correct function get_user_by_username
    user = user_crud.get_user_by_username(db, username=token_data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user