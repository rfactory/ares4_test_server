from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.core.exceptions import NotFoundError, AppLogicError

# --- Inter-Domain Providers and Schemas ---
from app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_command_providers
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider

class RejectRequestPolicy:
    def execute(self, db: Session, *, request_id: int, admin_user: User):
        """
        접근 요청 거부 워크플로우를 조율합니다.
        1. 요청 객체를 조회합니다.
        2. 요청의 유효성을 검증합니다.
        3. 요청 상태를 'rejected'로 업데이트합니다.
        4. 트랜잭션을 커밋합니다.
        """
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

        # 4. 트랜잭션 커밋
        db.commit()

        return updated_request

reject_request_policy = RejectRequestPolicy()
