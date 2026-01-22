from typing import Optional, List

from app.core.exceptions import NotFoundError, AppLogicError
from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.organization import Organization
from app.models.objects.access_request import AccessRequest
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestInvite

class InvitationPreconditionValidator:
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
        """사전 조회된 데이터를 기반으로 초대 수락에 대한 모든 전제조건을 검증합니다."""
        
        if not db_user_to_invite:
            raise NotFoundError("User", invitation_in.email_to_invite)

        if not db_role:
            raise NotFoundError("Role", str(invitation_in.role_id))

        if invitation_in.organization_id and not db_organization:
            raise NotFoundError("Organization", str(invitation_in.organization_id))

        # 사용자가 해당 컨텍스트에 이미 어떤 역할이든 가지고 있는지 확인합니다.
        for assignment in existing_assignments:
            if assignment.organization_id == invitation_in.organization_id:
                raise AppLogicError("User already has a role in the specified context. Please update the existing role instead of inviting.")

        if existing_pending_request:
            raise AppLogicError("A pending invitation or request for this user and role already exists.")

invitation_precondition_validator = InvitationPreconditionValidator()
