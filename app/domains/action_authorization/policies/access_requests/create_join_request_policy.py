from sqlalchemy.orm import Session
from typing import Optional

from app.core.exceptions import NotFoundError, AppLogicError
from app.models.objects.user import User
from app.models.objects.role import Role
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.services.access_requests.schemas.access_request_command import AccessRequestCreate
from app.domains.services.access_requests.services.access_request_command_service import access_request_command_service
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class CreateJoinRequestPolicy:
    def execute(
        self,
        db: Session,
        *,
        requester_user: User,
        org_identifier: str,
        reason: Optional[str]
    ):
        """사용자의 조직 가입 요청 전체 워크플로우를 조율합니다."""
        # 1. 조직 검색
        org = organization_query_provider.find_organization_by_identifier(db, identifier=org_identifier)
        if not org:
            raise NotFoundError(resource="Organization", resource_id=org_identifier)

        # 2. 조직의 기본 Admin 역할(tier=1) 조회
        admin_roles = role_query_provider.get_roles_by_organization_id_and_tier(db, organization_id=org.id, tier=1)
        if len(admin_roles) != 1:
            raise AppLogicError(
                f"Default admin role (tier=1) for organization '{org.company_name}' is not uniquely defined."
            )
        admin_role = admin_roles[0]

        # 3. 요청 생성을 위한 서비스 호출
        request_in = AccessRequestCreate(
            reason=reason,
            requested_role_id=admin_role.id,
            organization_id=org.id,
            user_id=requester_user.id
        )
        created_request = access_request_command_service.create_access_request(
            db, 
            request_in=request_in, 
            user_id=requester_user.id, 
            actor_user=requester_user,
            type="pull",  # 사용자가 직접 요청하므로 'pull' 방식
            initiated_by_user_id=requester_user.id  # 요청 주체는 사용자 본인
        )
        
        # 4. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="JOIN_REQUEST_CREATED",
            description=f"User {requester_user.username} requested to join organization {org.company_name}",
            actor_user=requester_user,
            details={
                "organization_id": org.id,
                "requested_role_id": admin_role.id,
                "reason": reason,
                "access_request_id": created_request.id
            }
        )
        
        # 5. 트랜잭션 커밋
        db.commit()

create_join_request_policy = CreateJoinRequestPolicy()