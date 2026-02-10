import logging
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, timezone

# --- Core Imports ---
from app.core.config import settings
from app.core.exceptions import NotFoundError, AppLogicError
from app.core.utils import generate_random_code

# --- Model Imports ---
from app.models.objects.user import User
from app.models.objects.role import Role  # [추가] 타입 인식을 위해 필요
from app.models.objects.access_request import AccessRequest # [추가]

# --- Inter-Domain Schema Imports ---
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestInvite, AccessRequestCreate
from app.domains.inter_domain.send_email.schemas.send_email_command import EmailSchema
from app.domains.services.organizations.schemas.organization_query import OrganizationResponse # [추가]

# --- Inter-Domain Provider Imports ---
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.validators.invitation_precondition.provider import invitation_precondition_validator_provider
from app.domains.inter_domain.validators.governance.governance_validator_provider import governance_validator_provider
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_command_providers
from app.domains.inter_domain.send_email.send_email_command_provider import send_email_command_provider
from app.domains.inter_domain.validators.headcount.headcount_validator_provider import headcount_validator_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class CreateInvitationPolicy:
    async def execute(self, db: Session, *, actor_user: User, invitation_in: AccessRequestInvite) -> AccessRequest:
        """
        관리자가 사용자를 역할로 초대(push)하는 워크플로우를 관장합니다.
        """
        try:
            # 1. 권한 검증
            permission_validator_provider.validate_for_role_assignment(db, user=actor_user, organization_id=invitation_in.organization_id)

            # 2. 데이터 조회 (Organization)
            db_organization: Optional[OrganizationResponse] = None
            if invitation_in.organization_id:
                org_query_svc = organization_query_provider.get_service()
                # 인자 이름을 org_id로 맞춤
                db_organization = org_query_svc.get_organization_by_id(db, org_id=invitation_in.organization_id)

            # 2. 데이터 조회 (User & Role)
            user_query_svc = user_identity_query_provider.get_service()
            db_user_to_invite: Optional[User] = user_query_svc.get_user_by_email(db, email=invitation_in.email_to_invite)
            
            role_query_svc = role_query_provider.get_service()
            db_role: Role = role_query_svc.get_role(db, role_id=invitation_in.role_id)

            if not db_role:
                raise NotFoundError("Role", str(invitation_in.role_id))

            # 3. 거버넌스 규칙 검증
            matching_rules = governance_query_provider.get_matching_rules(
                db=db, actor_user=actor_user, action="assign_role", context=db_role.scope, target_role=db_role
            )
            current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=db_role.id)
            prime_admin_count = governance_query_provider.get_prime_admin_count(db)

            governance_validator_provider.evaluate_rule(
                actor_user=actor_user,
                matching_rules=matching_rules,
                target_role=db_role,
                current_headcount=current_headcount,
                prime_admin_count=prime_admin_count
            )

            # 4. 인원수 제한 검증
            headcount_validator_provider.validate(
                role_name=db_role.name,
                current_headcount=current_headcount,
                max_headcount=db_role.max_headcount
            )
            
            # User가 존재할 경우에만 할당 및 요청 조회
            existing_assignments = []
            existing_pending_request = None
            if db_user_to_invite:
                existing_assignments = user_role_assignment_query_provider.get_assignments_for_user(db, user_id=db_user_to_invite.id)
                existing_pending_request = access_request_query_provider.get_pending_by_user_role_org(
                    db, user_id=db_user_to_invite.id, requested_role_id=invitation_in.role_id, organization_id=invitation_in.organization_id
                )

            # 5. 유효성 검사 위임
            invitation_precondition_validator_provider.validate(
                db_user_to_invite=db_user_to_invite,
                db_role=db_role,
                db_organization=db_organization,
                existing_assignments=existing_assignments,
                existing_pending_request=existing_pending_request,
                invitation_in=invitation_in
            )

            # 6. AccessRequest 생성 로직 구현
            verification_code = generate_random_code()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.INVITATION_EXPIRATION_HOURS)
            
            access_request_create_in = AccessRequestCreate(
                requested_role_id=invitation_in.role_id,
                organization_id=invitation_in.organization_id,
                reason=invitation_in.reason if invitation_in.reason else f"Invitation from {actor_user.username}",
            )
            
            # [수정] db_user_to_invite가 None일 경우에 대한 방어 로직 (Precondition에서 걸러지겠지만 타입 안전을 위해)
            target_user_id = db_user_to_invite.id if db_user_to_invite else None

            created_access_request = access_request_command_providers.create_access_request(
                db=db, 
                request_in=access_request_create_in,
                user_id=target_user_id,
                actor_user=actor_user,
                type="push",
                initiated_by_user_id=actor_user.id,
                verification_code=verification_code,
                verification_code_expires_at=expires_at
            )

            # 7. 이메일 발송 로직 구현 (db_organization이 Response DTO이므로 .company_name 인식됨)
            email_data = EmailSchema(
                to=db_user_to_invite.email if db_user_to_invite else invitation_in.email_to_invite,
                subject="[Ares] You have been invited to a role",
                template_name="role_invitation.html",
                context={
                    "invited_username": db_user_to_invite.username if db_user_to_invite else "User",
                    "inviting_admin": actor_user.username,
                    "role_name": db_role.name,
                    "organization_name": db_organization.company_name if db_organization else "System",
                    "verification_code": verification_code,
                    "expiration_hours": settings.INVITATION_EXPIRATION_HOURS
                }
            )
            await send_email_command_provider.send_email(email_data=email_data)
            
            # 8. 감사 로그 기록
            audit_command_provider.log(
                db=db,
                event_type="INVITATION_CREATED",
                description=f"Admin {actor_user.username} invited {invitation_in.email_to_invite} to role {db_role.name}",
                actor_user=actor_user,
                details={
                    "invited_email": invitation_in.email_to_invite,
                    "role_id": db_role.id,
                    "org_id": invitation_in.organization_id
                }
            )
            
            # 9. 트랜잭션 커밋
            db.commit()

            return created_access_request

        except Exception as e:
            db.rollback()
            logger.error(f"POLICY_ERROR: Invitation failed: {e}", exc_info=True)
            raise e

create_invitation_policy = CreateInvitationPolicy()