from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import SessionLocal
from app.core import security
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.user_identity.schemas.models import User

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
    
    user = user_identity_query_provider.get_user_by_username(db, username=token_data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user