from sqlalchemy.orm import Session
from datetime import datetime

from app.models.objects.user import User


def set_2fa_code_in_db(db: Session, *, user: User, code: str, expires_at: datetime) -> User:
    """
    사용자 모델에 2FA 코드와 만료 시간을 설정합니다.
    """
    user.email_verification_token = code
    user.email_verification_token_expires_at = expires_at
    db.add(user)
    return user


def clear_2fa_code_in_db(db: Session, *, user: User) -> User:
    """
    사용자 모델의 2FA 관련 필드를 None으로 설정합니다.
    """
    user.email_verification_token = None
    user.email_verification_token_expires_at = None
    db.add(user)
    return user
