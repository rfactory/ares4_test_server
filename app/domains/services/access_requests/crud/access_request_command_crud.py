# 2. app/domains/services/access_requests/crud/access_request_command_crud.py
from sqlalchemy.orm import Session
from app.core.crud_base import CRUDBase
from app.models.objects.access_request import AccessRequest
from ..schemas.access_request_command import AccessRequestCreate, AccessRequestUpdate

class CRUDAccessRequestCommand(CRUDBase[AccessRequest, AccessRequestCreate, AccessRequestUpdate]):
    def create(self, db: Session, *, request_in: AccessRequestCreate, user_id: int) -> AccessRequest:
        db_obj = AccessRequest(
            user_id=user_id,
            requested_role_id=request_in.requested_role_id,
            organization_id=request_in.organization_id,
            reason=request_in.reason,
            status="pending"
        )
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

access_request_crud_command = CRUDAccessRequestCommand(AccessRequest)