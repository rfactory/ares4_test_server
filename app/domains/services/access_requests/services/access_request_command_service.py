# 파일 경로: app/domains/services/access_requests/services/access_request_command_service.py

from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User as DBUser
from app.models.objects.access_request import AccessRequest
from app.core.exceptions import NotFoundError

# CRUD와 스키마를 import 합니다.
from ..crud.access_request_command_crud import access_request_command_crud
from ..crud.access_request_query_crud import access_request_crud_query
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
        actor_user: DBUser
    ) -> AccessRequest:
        """새로운 접근 요청을 생성하고 감사 로그를 기록합니다."""
        # 1. CRUD를 통해 데이터베이스에 객체 생성
        db_obj = access_request_command_crud.create(db, obj_in=request_in, user_id=user_id)
        db.flush()

        # 2. 감사 로그 기록
        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="AccessRequest",
            resource_id=db_obj.id,
            new_value=db_obj.as_dict()
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
        """접근 요청의 상태를 업데이트하고 감사 로그를 기록합니다."""
        # 1. 업데이트할 객체를 조회
        db_obj = access_request_crud_query.get(db, id=request_id)
        if not db_obj:
            raise NotFoundError("AccessRequest", str(request_id))

        old_value = db_obj.as_dict()

        # 2. CRUD를 통해 객체 업데이트
        updated_obj = access_request_command_crud.update(db, db_obj=db_obj, obj_in=update_in)
        db.flush()

        # 3. 감사 로그 기록
        audit_command_provider.log_update(
            db=db,
            actor_user=admin_user,
            resource_name="AccessRequest",
            resource_id=updated_obj.id,
            old_value=old_value,
            new_value=updated_obj.as_dict()
        )
        return updated_obj

    def delete_access_request(
        self,
        db: Session,
        *,
        request_id: int,
        actor_user: DBUser
    ) -> AccessRequest:
        """접근 요청을 삭제하고 감사 로그를 기록합니다."""
        # 1. 삭제할 객체를 조회
        db_obj = access_request_crud_query.get(db, id=request_id)
        if not db_obj:
            raise NotFoundError("AccessRequest", str(request_id))

        deleted_value = db_obj.as_dict()

        # 2. CRUD를 통해 객체 삭제
        deleted_obj = access_request_command_crud.remove(db, id=request_id)
        db.flush()

        # 3. 감사 로그 기록
        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="AccessRequest",
            resource_id=request_id,
            deleted_value=deleted_value
        )
        return deleted_obj

access_request_command_service = AccessRequestCommandService()
