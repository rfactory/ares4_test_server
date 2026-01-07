from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.organization import Organization
from app.models.objects.access_request import AccessRequest
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestInvite
from app.domains.action_authorization.validators.invitation_precondition.validator import invitation_precondition_validator

class InvitationPreconditionValidatorProvider:
    def validate(
        self,
        *,
        db_user_to_invite: Optional[User],
        db_role: Optional[Role],
        db_organization: Optional[Organization],
        existing_assignments: List[UserOrganizationRole],
        existing_pending_request: Optional[AccessRequest],
        invitation_in: AccessRequestInvite
    ):
        invitation_precondition_validator.validate(
            db_user_to_invite=db_user_to_invite,
            db_role=db_role,
            db_organization=db_organization,
            existing_assignments=existing_assignments,
            existing_pending_request=existing_pending_request,
            invitation_in=invitation_in
        )

invitation_precondition_validator_provider = InvitationPreconditionValidatorProvider()
