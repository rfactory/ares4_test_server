from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.objects.access_request import AccessRequest
from ..schemas.access_request import AccessRequestCreate, AccessRequestUpdate

class CRUDAccessRequest:
    def create(self, db: Session, *, request_in: AccessRequestCreate, user_id: int, organization_id: Optional[int] = None) -> AccessRequest:
        
        db_obj = AccessRequest(
            email=request_in.email,
            user_id=user_id, # Directly use the provided user_id
            requested_role_id=request_in.requested_role_id,
            organization_id=organization_id, # Use provided organization_id
            reason=request_in.reason,
            status="pending"
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, *, request_id: int) -> Optional[AccessRequest]:
        return db.query(AccessRequest).filter(AccessRequest.id == request_id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = "pending", 
        user_id: Optional[int] = None, 
        requested_role_id: Optional[int] = None, 
        organization_id: Optional[int] = None
    ) -> List[AccessRequest]:
        query = db.query(AccessRequest)
        if status:
            query = query.filter(AccessRequest.status == status)
        if user_id:
            query = query.filter(AccessRequest.user_id == user_id)
        if requested_role_id:
            query = query.filter(AccessRequest.requested_role_id == requested_role_id)
        if organization_id:
            query = query.filter(AccessRequest.organization_id == organization_id)
        return query.order_by(AccessRequest.created_at.desc()).offset(skip).limit(limit).all()

    def update_status(
        self, 
        db: Session, 
        *, 
        db_obj: AccessRequest, 
        update_in: AccessRequestUpdate, 
        admin_user_id: int
    ) -> AccessRequest:
        db_obj.status = update_in.status
        db_obj.reviewed_by_user_id = admin_user_id
        db_obj.reviewed_at = datetime.now(timezone.utc)
        db_obj.rejection_reason = update_in.rejection_reason # Can be None if approved
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

access_request_crud = CRUDAccessRequest()