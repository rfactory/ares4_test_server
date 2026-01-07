from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone 

from app.models.objects.user import User
from app.core.exceptions import NotFoundError, AppLogicError
from app.core.utils import generate_random_code

# --- Inter-Domain Providers and Schemas ---
from app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_command_providers
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider
from app.domains.inter_domain.send_email.send_email_command_provider import send_email_command_provider
from app.domains.inter_domain.send_email.schemas.send_email_command import EmailSchema
from app.domains.services.access_requests.schemas.access_request_command import AccessRequestUpdate # 서비스 스키마 임포트

class ApproveRequestPolicy:
    def execute(self, db: Session, *, request_id: int, admin_user: User):
        """
        접근 요청 승인 워크플로우를 조율합니다.
        1. 요청 객체를 조회합니다.
        2. 요청의 유효성을 검증합니다.
        3. 요청 상태를 'approved'로 업데이트하고 인증 코드를 생성합니다.
        4. 사용자에게 승인 및 인증 코드 이메일을 발송합니다.
        5. 트랜잭션을 커밋합니다.
        """
        # 1. 요청 객체 조회
        db_access_request = access_request_query_provider.get_access_request_by_id(db, request_id=request_id)
        if not db_access_request:
            raise NotFoundError("AccessRequest", str(request_id))

        # 2. 요청 유효성 검증
        if db_access_request.status != "pending":
            raise AppLogicError(f"Access request ID {request_id} is not pending. Current status: {db_access_request.status}")

        # 3. 인증 코드 생성 및 DB 업데이트 준비
        verification_code = generate_random_code()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1) # 1시간 유효

        update_in = AccessRequestUpdate(
            status="approved",
            reviewed_by_user_id=admin_user.id,
            reviewed_at=datetime.now(timezone.utc),
            verification_code=verification_code,
            verification_code_expires_at=expires_at
        )

        # 4. 요청 상태 업데이트 서비스 호출
        updated_request = access_request_command_providers.update_access_request_status(
            db=db, db_obj=db_access_request, update_in=update_in, admin_user=admin_user
        )

        # 5. 이메일 발송
        email_data = EmailSchema(
            to=updated_request.user.email,
            subject="[Ares] Access Request Approved",
            template_name="access_request_approval.html",
            context={
                "requester_username": updated_request.user.username,
                "organization_name": updated_request.organization.company_name if updated_request.organization else "System",
                "role_name": updated_request.requested_role.name,
                "verification_code": verification_code
            }
        )
        send_email_command_provider.send_email(email_data=email_data)

        # 6. 트랜잭션 커밋
        db.commit()

        return updated_request

approve_request_policy = ApproveRequestPolicy()
