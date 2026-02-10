import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

# inter_domain Provider를 통해 접근 요청 정보를 조회합니다.
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider

logger = logging.getLogger(__name__)

class DuplicatePermissionRequestValidator:
    def validate(
        self, db: Session, *, user_id: int, organization_id: Optional[int] # requested_role_id 제거
    ) -> Tuple[bool, Optional[str]]:
        """
        한 사용자가 특정 조직에 대해 보류 중인(pending) 접근 요청을 이미 가지고 있는지 확인합니다.
        """
        existing_request = access_request_query_provider.get_pending_access_request_by_user_org(
            db,
            user_id=user_id,
            organization_id=organization_id
        )

        if existing_request:
            logger.warning(f"Validation check: Duplicate pending access request found for user ID {user_id}, organization ID {organization_id}.")
            return False, f"A pending request for a role already exists for user (ID: {user_id}) within this organization." # 메시지 수정
        
        return True, None

duplicate_permission_request_validator = DuplicatePermissionRequestValidator()
