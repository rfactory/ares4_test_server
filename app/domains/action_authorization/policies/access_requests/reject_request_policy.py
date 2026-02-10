import logging
from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.core.exceptions import NotFoundError, AppLogicError

# --- Inter-Domain Providers and Schemas ---
from app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_command_providers
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class RejectRequestPolicy:
    def execute(self, db: Session, *, request_id: int, admin_user: User):
        """
        접근 요청 거부 워크플로우를 조율합니다.
        1. 요청 객체를 조회합니다.
        2. 요청의 유효성을 검증합니다.
        3. 요청 상태를 'rejected'로 업데이트합니다.
        4. 감사 로그를 기록하고 트랜잭션을 커밋합니다.
        """
        try:
            # 1. 요청 객체 조회
            db_access_request = access_request_query_provider.get_access_request_by_id(db, request_id=request_id)
            if not db_access_request:
                raise NotFoundError("AccessRequest", str(request_id))

            # 2. 요청 유효성 검증
            if db_access_request.status != "pending":
                raise AppLogicError(f"Access request ID {request_id} is not pending. Current status: {db_access_request.status}")

            # 3. 요청 거부 서비스 호출
            updated_request = access_request_command_providers.reject_access_request(
                db=db, db_obj=db_access_request, admin_user=admin_user
            )
            
            # [Ares Aegis] 4. 감사 로그 기록
            audit_command_provider.log(
                db=db,
                event_type="ACCESS_REQUEST_REJECTED",
                description=f"Admin {admin_user.username} rejected access request {request_id}",
                actor_user=admin_user,
                details={
                    "request_id": request_id, 
                    "target_user_id": db_access_request.user_id
                }
            )
            
            # 5. 트랜잭션 최종 커밋
            db.commit()
            logger.info(f"POLICY: Access request {request_id} rejected and committed.")

            return updated_request

        except Exception as e:
            # 실패 시 롤백 수행
            db.rollback()
            logger.error(f"POLICY_ERROR: Failed to reject request {request_id}: {e}", exc_info=True)
            raise e

reject_request_policy = RejectRequestPolicy()