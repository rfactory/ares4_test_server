# domains/services/user_identity/validators/user_update_validators.py

from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.exceptions import DuplicateEntryError
from app.core.security import get_password_hash
from app.models.objects.user import User as DBUser
from ..crud.user_identity_query_crud import user_identity_query_crud

# --- Individual Validator and Transformer Functions ---

def validate_username(db: Session, db_user: DBUser, new_username: str) -> None:
    """사용자 이름 변경 시 중복을 확인합니다."""
    if new_username != db_user.username and user_identity_query_crud.get_by_username(db, username=new_username):
        raise DuplicateEntryError("User", "username", new_username)

def validate_email(db: Session, db_user: DBUser, new_email: str) -> None:
    """이메일 변경 시 중복을 확인합니다."""
    if new_email != db_user.email and user_identity_query_crud.get_by_email(db, email=new_email):
        raise DuplicateEntryError("User", "email", new_email)

def transform_password(update_data: Dict[str, Any]) -> None:
    """비밀번호가 있는 경우 해시 처리하고 원본은 삭제합니다."""
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]

# --- Dispatchers ---

# 유효성 검사기 디스패처
# 키: 모델 필드 이름, 값: 검증 함수
USER_UPDATE_VALIDATORS = {
    "username": validate_username,
    "email": validate_email,
}

# 데이터 변환기 디스패처
# 키: 스키마 필드 이름, 값: 변환 함수
USER_UPDATE_TRANSFORMERS = {
    "password": transform_password,
}
