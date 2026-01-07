from typing import Optional

from app.models.objects.user import User
from app.models.objects.access_request import AccessRequest
from app.domains.action_authorization.validators.invitation_acceptance.validator import invitation_acceptance_validator

class InvitationAcceptanceValidatorProvider:
    def validate(
        self,
        *,
        db_access_request: Optional[AccessRequest],
        accepting_user: User
    ):
        # AppLogicError 예외 처리는 호출하는 쪽(Policy)에서 담당
        invitation_acceptance_validator.validate(
            db_access_request=db_access_request,
            accepting_user=accepting_user
        )

invitation_acceptance_validator_provider = InvitationAcceptanceValidatorProvider()
