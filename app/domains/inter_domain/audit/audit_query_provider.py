from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.events_logs.audit_log import AuditLog
from app.domains.services.audit.services.audit_query_service import audit_query_service

class AuditQueryProvider:
    """
    audit_query_service의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def get_logs_with_filter(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        filter_condition: Optional[Dict[str, Any]] = None
    ) -> List[AuditLog]:
        """
        내부 audit_query_service를 호출하여 필터링된 로그를 가져옵니다.
        """
        return audit_query_service.get_logs_with_filter(
            db,
            skip=skip,
            limit=limit,
            filter_condition=filter_condition
        )

audit_query_provider = AuditQueryProvider()
