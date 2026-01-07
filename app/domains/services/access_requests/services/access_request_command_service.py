# 파일 경로: app/domains/services/access_requests/services/access_request_command_service.py

from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import datetime

from app.models.objects.user import User as DBUser
from app.models.objects.access_request import AccessRequest
from app.core.exceptions import NotFoundError, AppLogicError

# CRUD와 스키마를 import 합니다.
from ..crud.access_request_command_crud import access_request_crud_command
from ..schemas.access_request_command import AccessRequestCreate, AccessRequestUpdate

# 다른 도메인의 Provider를 import 합니다.
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class AccessRequestCommandService:
    """접근 요청의 생성, 수정, 삭제(Command)와 관련된 비즈니스 로직을 담당합니다."""

    def create_access_request(
        self,
        db: Session,
        *,
        request_in: AccessRequestCreate,
        user_id: int,
        actor_user: DBUser,
        type: Literal["push", "pull"],
        initiated_by_user_id: int,
        verification_code: Optional[str] = None,
        verification_code_expires_at: Optional[datetime] = None
    ) -> AccessRequest:
        """
        새로운 접근 요청을 생성하고 감사 로그를 기록합니다.
        """
        db_obj = access_request_crud_command.create(
            db, 
            request_in=request_in, 
            user_id=user_id, 
            type=type,
            initiated_by_user_id=initiated_by_user_id,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )
        db.flush()

        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="ACCESS_REQUEST_CREATED",
            description=f"Access request created for user_id {user_id}",
            details=db_obj.as_dict()
        )
        return db_obj

    def update_access_request_status(
        self,
        db: Session,
        *,
        request_id: int, 
        update_in: AccessRequestUpdate,
        admin_user: DBUser
    ) -> AccessRequest:
        """
        접근 요청의 상태를 업데이트하고 감사 로그를 기록합니다.
        """
        db_obj = access_request_crud_command.get(db, id=request_id)
        if not db_obj:
            raise NotFoundError(resource_name="AccessRequest", resource_id=str(request_id))
        
        old_value = db_obj.as_dict()

        updated_obj = access_request_crud_command.update(db, db_obj=db_obj, obj_in=update_in)
        db.flush()

        audit_command_provider.log(
            db=db,
            actor_user=admin_user,
            event_type="ACCESS_REQUEST_UPDATED",
            description=f"Access request {db_obj.id} status changed to {updated_obj.status}",
            details={"old_value": old_value, "new_value": updated_obj.as_dict()}
        )
        return updated_obj

    def delete_access_request(
        self,
        db: Session,
        *,
        db_obj: AccessRequest, # id 대신 객체를 직접 받음
        actor_user: DBUser
    ) -> AccessRequest:
        """
        접근 요청을 삭제하고 감사 로그를 기록합니다.
        """
        deleted_value = db_obj.as_dict()
        request_id = db_obj.id

        access_request_crud_command.remove(db, id=request_id)
        db.flush()

        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="ACCESS_REQUEST_DELETED",
            description=f"Access request {request_id} deleted.",
            details=deleted_value
        )
        return db_obj

access_request_command_service = AccessRequestCommandService()
