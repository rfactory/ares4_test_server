from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import datetime

from app.models.objects.user import User as DBUser
from app.models.objects.access_request import AccessRequest
from app.domains.services.access_requests.services.access_request_command_service import access_request_command_service, AccessRequestCommandService
from app.domains.services.access_requests.schemas.access_request_command import AccessRequestCreate, AccessRequestUpdate

class AccessRequestCommandProviders:
    def get_service(self) -> AccessRequestCommandService:
        return access_request_command_service
    
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
        """새로운 접근 요청 생성을 위한 안정적인 인터페이스를 제공합니다."""
        return access_request_command_service.create_access_request(
            db=db, 
            request_in=request_in, 
            user_id=user_id, 
            actor_user=actor_user,
            type=type,
            initiated_by_user_id=initiated_by_user_id,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )

    def update_access_request_status(
        self, 
        db: Session, 
        *,
        db_obj: AccessRequest, 
        update_in: AccessRequestUpdate, 
        admin_user: DBUser
    ) -> AccessRequest:
        """접근 요청 상태 업데이트를 위한 안정적인 인터페이스를 제공합니다."""
        return access_request_command_service.update_access_request_status(
            db=db, 
            db_obj=db_obj,
            update_in=update_in, 
            admin_user=admin_user
        )
        
    def reject_access_request(
        self,
        db: Session,
        *,
        db_obj: AccessRequest,
        admin_user: DBUser
    ) -> AccessRequest:
        """접근 요청을 거부(rejected) 상태로 변경합니다."""
        update_in = AccessRequestUpdate(status="rejected")
        return access_request_command_service.update_access_request_status(
            db=db,
            db_obj=db_obj,
            update_in=update_in,
            admin_user=admin_user
        )

    def delete_access_request(self, db: Session, *, db_obj: AccessRequest, actor_user: DBUser) -> AccessRequest:
        """접근 요청 삭제를 위한 안정적인 인터페이스를 제공합니다."""
        return access_request_command_service.delete_access_request(
            db=db, 
            db_obj=db_obj, 
            actor_user=actor_user
        )

access_request_command_providers = AccessRequestCommandProviders()