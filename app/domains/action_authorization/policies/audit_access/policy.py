import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional, List, Any

from app.models.objects.user import User
from app.models.events_logs.audit_log import AuditLog

# 의존성: 활성 컨텍스트 프로바이더 (가상)
from app.dependencies import get_active_context, ActiveContext

# 의존성: 범용 권한 검증기
from ...validators.permission.validator import permission_validator

# 의존성: 데이터 조회를 위한 서비스
from app.domains.services.audit_query.services.audit_query_service import audit_query_service

# 이 Policy가 사용할 특정 권한 이름들
AUDIT_READ_FULL = "audit:read:full"
AUDIT_READ_GENERAL = "audit:read:general"
AUDIT_READ_TECHNICAL = "audit:read:technical"

logger = logging.getLogger(__name__)

class AuditAccessPolicy:
    """
    감사 로그 조회에 대한 인가 정책을 정의하고 실행합니다.
    """

    def get_logs(
        self,
        db: Session,
        *, 
        current_user: User,
        active_context: ActiveContext, # API 계층에서 주입된 활성 컨텍스트
        skip: int,
        limit: int
    ) -> List[AuditLog]:
        """
        계층적 인가 흐름에 따라 감사 로그를 조회합니다.
        1. 컨텍스트 확인 -> 2. 권한 확인 -> 3. 서비스 호출
        """
        # 1. 컨텍스트 유효성 검사: 시스템 관리자 컨텍스트인지 확인
        if active_context.type != "SYSTEM_ADMINISTRATOR":
            logger.warning(f"User (ID: {current_user.id}) tried to access audit logs outside of SYSTEM_ADMINISTRATOR context.")
            return []

        # 2. 권한 확인 (우선순위: full > general > technical)
        can_read_full, _ = permission_validator.validate(db, user=current_user, permission_name=AUDIT_READ_FULL)
        if can_read_full:
            # filter_condition이 없으므로 None 전달
            return audit_query_service.get_logs_with_filter(db, skip=skip, limit=limit, filter_condition=None)

        can_read_general, _ = permission_validator.validate(db, user=current_user, permission_name=AUDIT_READ_GENERAL)
        if can_read_general:
            # 향후 마스킹 등을 위해 분리. 현재는 필터 없이 모든 로그 조회.
            return audit_query_service.get_logs_with_filter(db, skip=skip, limit=limit, filter_condition=None)

        can_read_technical, _ = permission_validator.validate(db, user=current_user, permission_name=AUDIT_READ_TECHNICAL)
        if can_read_technical:
            # 이 권한에 연결된 동적 필터를 DB에서 가져오는 로직 (향후 구현)
            # filter_condition = get_filter_for_permission(db, permission_name=AUDIT_READ_TECHNICAL)
            # 현재는 하드코딩된 예시 필터 사용
            example_filter = {"event_type": "SYSTEM_ERROR"}
            return audit_query_service.get_logs_with_filter(db, skip=skip, limit=limit, filter_condition=example_filter)
        
        # 어떤 관련 권한도 없는 경우
        logger.warning(f"User (ID: {current_user.id}) in SYSTEM_ADMINISTRATOR context has no permission to read audit logs.")
        return []

audit_access_policy = AuditAccessPolicy()
