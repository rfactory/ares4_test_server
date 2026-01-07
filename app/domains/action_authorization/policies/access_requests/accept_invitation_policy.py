from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.role import Role
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider
from app.domains.inter_domain.validators.invitation_acceptance.provider import invitation_acceptance_validator_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_command_provider import user_role_assignment_command_provider
from app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_command_providers
from app.domains.inter_domain.validators.headcount.headcount_validator_provider import headcount_validator_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.governance.governance_command_provider import governance_command_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider

# Import schemas from inter_domain
from app.domains.inter_domain.user_role_assignment.schemas.user_role_assignment_command import UserRoleAssignmentCreate
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestUpdate

class AcceptInvitationPolicy:
    async def execute(self, db: Session, *, accepting_user: User, verification_code: str):
        """
        사용자가 인증 코드를 사용하여 역할 초대를 수락하는 워크플로우를 관장합니다.
        """
        # 1. 데이터 조회
        request_schema = access_request_query_provider.get_by_verification_code(db, code=verification_code)

        # 2. 유효성 검사 위임
        invitation_acceptance_validator_provider.validate(
            db_access_request=request_schema,
            accepting_user=accepting_user
        )

        # 3. 역할 할당 전 추가 검증 (Headcount)
        role_to_assign = role_query_provider.get_role(db, role_id=request_schema.requested_role_id)
        current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=role_to_assign.id)
        headcount_validator_provider.validate(
            role_name=role_to_assign.name,
            current_headcount=current_headcount,
            max_headcount=role_to_assign.max_headcount
        )

        # 4. 역할 할당
        assignment_in = UserRoleAssignmentCreate(
            user_id=accepting_user.id,
            role_id=request_schema.requested_role_id,
            organization_id=request_schema.organization_id
        )
        new_assignment = user_role_assignment_command_provider.assign_role(
            db, 
            assignment_in=assignment_in,
            request_user=accepting_user
        )

        # 5. 요청 상태 업데이트
        update_in = AccessRequestUpdate(
            status="completed",
            verification_code=None, # 코드 비활성화
            verification_code_expires_at=None
        )
        updated_request = access_request_command_providers.update_access_request_status(
            db=db, 
            request_id=request_schema.id, 
            update_in=update_in,
            admin_user=accepting_user
        )

        # 6. 후속 조치 (비상 모드 확인)
        governance_command_provider.check_and_update_emergency_mode(db, roles_changed=[role_to_assign])
        
        db.commit()

        return new_assignment

accept_invitation_policy = AcceptInvitationPolicy()
