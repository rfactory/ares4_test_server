# 2. app/domains/services/access_requests/crud/access_request_command_crud.py
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Literal

from app.core.crud_base import CRUDBase
from ..schemas.access_request_command import AccessRequestCreate, AccessRequestUpdate

from app.models.objects.access_request import AccessRequest

# CRUDAccessRequestCommand 클래스를 먼저 정의합니다.
class CRUDAccessRequestCommand(CRUDBase['AccessRequest', AccessRequestCreate, AccessRequestUpdate]):
    def create(
        self, 
        db: Session, 
        *, 
        request_in: AccessRequestCreate, 
        user_id: int,
        initiated_by_user_id: int, 
        type: Literal["push", "pull"],
        verification_code: Optional[str] = None,
        verification_code_expires_at: Optional[datetime] = None
    ) -> 'AccessRequest':
        # AccessRequest 모델은 함수 내부에서 임포트하여 순환 참조를 방지합니다.
        from app.models.objects.access_request import AccessRequest

        db_obj = AccessRequest(
            user_id=user_id,
            requested_role_id=request_in.requested_role_id,
            organization_id=request_in.organization_id,
            reason=request_in.reason,
            status="pending",
            type=type,
            initiated_by_user_id=initiated_by_user_id,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

# 인스턴스는 클래스 정의 후에 생성합니다.
# from app.models.objects.access_request import AccessRequest
access_request_crud_command = CRUDAccessRequestCommand(AccessRequest)