from typing import Optional
from datetime import datetime, timezone

from app.core.exceptions import AppLogicError, NotFoundError
from app.models.objects.user import User
from app.models.objects.access_request import AccessRequest

class InvitationAcceptanceValidator:
    def validate(
        self,
        *,
        db_access_request: Optional[AccessRequest],
        accepting_user: User
    ):
        """사전 조회된 데이터를 기반으로 초대 수락에 대한 모든 전제조건을 검증합니다."""

        if not db_access_request:
            raise NotFoundError("Invitation/Request", "(with provided code)")

        if db_access_request.user_id != accepting_user.id:
            raise AppLogicError("This invitation is not for you.")

        if db_access_request.type != 'push' or db_access_request.status != 'pending':
            raise AppLogicError("This invitation is no longer valid or has already been processed.")

        if db_access_request.verification_code_expires_at < datetime.now(timezone.utc):
            raise AppLogicError("The verification code has expired.")

invitation_acceptance_validator = InvitationAcceptanceValidator()
