from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.events_logs.audit_log import AuditLog


class CRUDAuditLogQuery:
    """
    데이터베이스에서 AuditLog 정보를 조회하는 클래스입니다.
    모든 메소드는 읽기 전용(read-only)입니다.
    """
    def get(self, db: Session, audit_log_id: int) -> Optional[AuditLog]:
        """ID를 기준으로 특정 AuditLog를 조회합니다."""
        return db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()

    def get_multi_with_filter(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        filter_condition: Optional[Dict[str, Any]] = None
    ) -> List[AuditLog]:
        """여러 AuditLog를 페이징하고 동적 필터를 적용하여 조회합니다."""
        query = db.query(AuditLog)

        if filter_condition:
            query = query.filter_by(**filter_condition)

        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """특정 사용자가 생성한 AuditLog를 페이징하여 조회합니다."""
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_event_type(self, db: Session, event_type: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """특정 이벤트 타입의 AuditLog를 페이징하여 조회합니다."""
        return db.query(AuditLog).filter(AuditLog.event_type == event_type).offset(skip).limit(limit).all()

audit_log_query_crud = CRUDAuditLogQuery()
