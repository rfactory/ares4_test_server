# app/domains/services/audit/crud/audit_command_crud.py
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.events_logs.audit_log import AuditLog
from app.models.events_logs.audit_log_detail import AuditLogDetail
from ..schemas.audit_command import AuditLogCreate, AuditLogDetailCreate


class CRUDAuditLogCommand:
    """AuditLog + Detail 한 번에 생성 (N+1 완전 해결)"""

    def create_with_details(
        self,
        db: Session,
        *,
        obj_in: AuditLogCreate,
        actor_user_id: Optional[int] = None
    ) -> AuditLog:
        db_log = AuditLog(
            event_type=obj_in.event_type,
            log_level=obj_in.log_level or "INFO",
            description=obj_in.description,
            user_id=actor_user_id,
        )
        db.add(db_log)
        db.flush()  # ← ID 생성

        if obj_in.details:
            detail_objects: List[AuditLogDetail] = [
                AuditLogDetail(
                    audit_log_id=db_log.id,
                    detail_key=item.detail_key,
                    detail_value=item.detail_value,
                    detail_value_type=item.detail_value_type,
                    description=item.description,
                )
                for item in obj_in.details
            ]
            db.bulk_save_objects(detail_objects)  # ← N+1 → 1쿼리

        db.flush()
        return db_log


# 기존 이름 유지 (기존 코드 호환성 100%)
audit_command_crud = CRUDAuditLogCommand()