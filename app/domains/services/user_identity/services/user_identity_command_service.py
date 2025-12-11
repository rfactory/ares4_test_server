from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ..crud.user_identity_command_crud import user_identity_command_crud
from ..crud.user_identity_query_crud import user_identity_query_crud
from ..schemas.user_identity_command import UserCreate, UserUpdate
from ..validators.user_update_validators import USER_UPDATE_VALIDATORS, USER_UPDATE_TRANSFORMERS
from app.core.security import get_password_hash
from app.models.objects.user import User as DBUser
from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class UserIdentityCommandService:
    async def create_user_and_log(self, db: Session, *, user_in: UserCreate, created_by: Optional[DBUser] = None, is_active: bool = True) -> DBUser:
        """새로운 사용자를 생성하고 감사 로그를 기록합니다."""
        if user_identity_query_crud.get_by_username(db, username=user_in.username):
            raise DuplicateEntryError("User", "username", user_in.username)
        if user_identity_query_crud.get_by_email(db, email=user_in.email):
            raise DuplicateEntryError("User", "email", user_in.email)

        create_data = {
            "username": user_in.username,
            "email": user_in.email,
            "password_hash": get_password_hash(user_in.password),
            "is_active": is_active
        }
        db_obj = user_identity_command_crud.create_with_hashed_password(db, create_data=create_data)

        audit_command_provider.log(
            db=db,
            event_type="USER_CREATED",
            description=f"New user '{db_obj.username}' created by {'system' if not created_by else created_by.username}. Active: {is_active}",
            actor_user=created_by if created_by else db_obj,
            target_user=db_obj,
            details={"email": db_obj.email}
        )
        return db_obj

    def update_user(self, db: Session, *, user_id: int, user_in: UserUpdate, actor_user: DBUser) -> DBUser:
        """사용자 정보를 업데이트합니다. Validator/Transformer 패턴을 사용합니다."""
        db_user = user_identity_query_crud.get(db, id=user_id)
        if not db_user:
            raise NotFoundError("User", str(user_id))
        
        old_value = db_user.as_dict()
        update_data = user_in.model_dump(exclude_unset=True)

        # 1. 데이터 변환 (e.g., 비밀번호 해싱)
        for field, func in USER_UPDATE_TRANSFORMERS.items():
            if field in update_data:
                func(update_data)

        # 2. 유효성 검사 (e.g., 사용자 이름, 이메일 중복 확인)
        for field, value in update_data.items():
            if field in USER_UPDATE_VALIDATORS:
                USER_UPDATE_VALIDATORS[field](db, db_user, value)
        
        updated_user = user_identity_command_crud.update(db, db_obj=db_user, obj_in=update_data)
        db.flush()

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="User",
            resource_id=updated_user.id,
            old_value=old_value,
            new_value=updated_user.as_dict()
        )
        return updated_user

    def delete_user(self, db: Session, *, user_id: int, actor_user: DBUser) -> DBUser:
        """사용자를 비활성화하여 soft-delete 처리하고, 감사 로그를 기록합니다."""
        db_user = user_identity_query_crud.get(db, id=user_id)
        if not db_user:
            raise NotFoundError("User", str(user_id))

        old_value = db_user.as_dict()
        
        # CRUD의 remove는 is_active=False로 설정하는 soft-delete로 구현되어 있음
        deactivated_user = user_identity_command_crud.remove(db, id=user_id)
        db.flush()

        # 비활성화는 상태 변경이므로 log_update 사용
        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="User",
            resource_id=deactivated_user.id,
            old_value=old_value,
            new_value=deactivated_user.as_dict()
        )
        return deactivated_user

    def activate_user(self, db: Session, *, user: DBUser, actor_user: Optional[DBUser]) -> DBUser:
        """사용자 계정을 활성화합니다."""
        old_value = user.as_dict()
        user.is_active = True
        db.add(user)
        db.flush()
        
        audit_command_provider.log_update(
            db=db,
            event_type="USER_ACTIVATED",
            resource_name="User",
            resource_id=user.id,
            actor_user=actor_user,
            old_value=old_value,
            new_value=user.as_dict()
        )
        return user

user_identity_command_service = UserIdentityCommandService()
