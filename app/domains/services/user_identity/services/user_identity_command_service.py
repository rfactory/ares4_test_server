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
    def get_password_hash(self, *, password: str) -> str:
        """비밀번호를 해시하여 반환합니다."""
        return get_password_hash(password)

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
            event_type="AUDIT",
            description=f"New user '{db_obj.username}' created by {'system' if not created_by else created_by.username}. Active: {is_active}",
            actor_user=created_by if created_by else db_obj,
            target_user=db_obj,
            details={"email": db_obj.email}
        )
        return db_obj

    def create_user_with_prehashed_password(self, db: Session, *, user_data: Dict[str, Any], is_active: bool = True) -> DBUser:
        """
        사전에 해시된 비밀번호를 사용하여 새로운 사용자를 생성하고 감사 로그를 기록합니다.
        (회원가입 완료 시나리오용)
        """
        create_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password_hash": user_data["hashed_password"],
            "is_active": is_active
        }
        db_obj = user_identity_command_crud.create_with_hashed_password(db, create_data=create_data)

        audit_command_provider.log(
            db=db,
            event_type="AUDIT",
            description=f"New user '{db_obj.username}' created after email verification.",
            actor_user=db_obj,
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

        for field, func in USER_UPDATE_TRANSFORMERS.items():
            if field in update_data:
                func(update_data)

        for field, value in update_data.items():
            if field in USER_UPDATE_VALIDATORS:
                USER_UPDATE_VALIDATORS[field](db, db_user, value)
        
        updated_user = user_identity_command_crud.update(db, db_obj=db_user, obj_in=update_data)
        db.flush()

        audit_command_provider.log(
            db=db,
            event_type="AUDIT",
            description=f"User '{updated_user.username}' (ID: {updated_user.id}) updated by '{actor_user.username}'.",
            actor_user=actor_user,
            target_user=updated_user,
            details={"old_value": old_value, "new_value": updated_user.as_dict()}
        )
        return updated_user

    def delete_user(self, db: Session, *, user_id: int, actor_user: DBUser) -> DBUser:
        """사용자를 비활성화하여 soft-delete 처리하고, 감사 로그를 기록합니다."""
        db_user = user_identity_query_crud.get(db, id=user_id)
        if not db_user:
            raise NotFoundError("User", str(user_id))

        # CRUD의 remove는 is_active=False로 설정하는 soft-delete로 구현되어 있음
        deactivated_user = user_identity_command_crud.remove(db, id=user_id)
        db.flush()

        audit_command_provider.log(
            db=db,
            event_type="AUDIT",
            description=f"User '{deactivated_user.username}' (ID: {user_id}) deactivated by '{actor_user.username}'.",
            actor_user=actor_user,
            target_user=deactivated_user
        )
        return deactivated_user

    def activate_user(self, db: Session, *, user: DBUser, actor_user: Optional[DBUser]) -> DBUser:
        """사용자 계정을 활성화합니다."""
        old_value = user.as_dict()
        user.is_active = True
        db.add(user)
        db.flush()
        
        audit_command_provider.log(
            db=db,
            event_type="AUDIT",
            description=f"User '{user.username}' (ID: {user.id}) activated by '{actor_user.username if actor_user else 'system'}'.",
            actor_user=actor_user,
            target_user=user,
            details={"old_value": old_value, "new_value": user.as_dict()}
        )
        return user

user_identity_command_service = UserIdentityCommandService()
