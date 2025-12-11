from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.events_logs.audit_log import AuditLog
from ..crud.audit_query_crud import audit_log_query_crud

class AuditQueryService:
    """
    감사 로그 조회와 관련된 순수한 데이터 접근 로직을 담당합니다.
    이 서비스는 권한이나 컨텍스트에 대해 알지 못합니다.
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
        Policy로부터 받은 동적 필터 조건을 사용하여 감사 로그를 조회합니다.
        """
        # CRUD 계층에 필터 조건을 그대로 전달합니다.
        return audit_log_query_crud.get_multi_with_filter(
            db,
            skip=skip,
            limit=limit,
            filter_condition=filter_condition
        )

audit_query_service = AuditQueryService()
