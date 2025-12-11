# app/domains/services/access_requests/access_requests_command_provider.py
# ← 이 파일만 아래처럼 고치면 됩니다

from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User as DBUser
from app.models.objects.access_request import AccessRequest
from app.domains.services.access_requests.services.access_request_command_service import access_request_command_service
from app.domains.services.access_requests.schemas.access_request_command import AccessRequestCreate, AccessRequestUpdate

class AccessRequestCommandProviders:
    def create_access_request(
        self, 
        db: Session, 
        *, 
        request_in: AccessRequestCreate, 
        user_id: int, 
        actor_user: DBUser   # ← 이거 추가 (Policy에서 넘겨줄 거임)
    ) -> AccessRequest:
        """새로운 접근 요청 생성을 위한 안정적인 인터페이스를 제공합니다."""
        return access_request_command_service.create_access_request(
            db=db, 
            request_in=request_in, 
            user_id=user_id, 
            actor_user=actor_user   # ← 이거 넘겨줘
        )

    def update_access_request_status(
        self, 
        db: Session, 
        *, 
        request_id: int, 
        update_in: AccessRequestUpdate, 
        admin_user: DBUser   # ← admin_user_id 대신 DBUser 객체로 받기
    ) -> AccessRequest:
        """접근 요청 상태 업데이트를 위한 안정적인 인터페이스를 제공합니다."""
        return access_request_command_service.update_access_request_status(
            db=db, 
            request_id=request_id, 
            update_in=update_in, 
            admin_user=admin_user
        )

    def delete_access_request(self, db: Session, *, request_id: int, actor_user: DBUser) -> AccessRequest:
        """접근 요청 삭제를 위한 안정적인 인터페이스를 제공합니다."""
        return access_request_command_service.delete_access_request(
            db=db, 
            request_id=request_id, 
            actor_user=actor_user
        )

access_request_command_providers = AccessRequestCommandProviders()