from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationCreate
from app.domains.inter_domain.validators.organization_business_registration_uniqueness.organization_business_registration_uniqueness_provider import organization_business_registration_uniqueness_provider
from app.domains.inter_domain.validators.organization_type_existence.organization_type_existence_provider import organization_type_existence_provider
from app.domains.inter_domain.organizations.organization_command_provider import organization_command_provider
# 역할 생성을 위한 임포트 추가
from app.domains.inter_domain.role_management.role_command_provider import role_command_provider
from app.domains.inter_domain.role_management.schemas.role_command import RoleCreate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class CreateOrganizationPolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        org_in: OrganizationCreate, 
        actor_user: User
    ) -> Organization:
        """
        새로운 조직을 생성하고 기본 관리자 역할을 포함하는 전체 비즈니스 로직을 지휘합니다.
        """
        # 권한 검증은 이제 API 엔드포인트의 PermissionChecker 의존성에 의해 처리됩니다.

        # 1. 비즈니스 규칙 검증
        is_unique = organization_business_registration_uniqueness_provider.validate(
            db, business_registration_number=org_in.business_registration_number
        )
        if not is_unique:
            raise DuplicateEntryError("Organization", "business_registration_number", org_in.business_registration_number)

        # ID로 조직 유형의 존재 여부를 확인합니다.
        type_exists = organization_type_existence_provider.validate(
            db, organization_type_id=org_in.organization_type_id
        )
        if not type_exists:
            raise NotFoundError("OrganizationType", str(org_in.organization_type_id))

        # 2. 조직 생성 실행
        new_org = organization_command_provider.create_organization(db, org_in=org_in, actor_user=actor_user)

        # 3. 해당 조직의 기본 Admin 역할 생성 (tier=1, max_headcount=2)
        admin_role_schema = RoleCreate(
            name="Admin",
            description=f"Default administrator role for {new_org.company_name}",
            scope="ORGANIZATION",
            organization_id=new_org.id,
            tier=1,
            max_headcount=2
        )
        role_command_provider.create_role(db, role_in=admin_role_schema, actor_user=actor_user)
        
        # 4. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="ORGANIZATION_CREATED",
            description=f"New organization '{new_org.company_name}' created by {actor_user.username}",
            actor_user=actor_user,
            details={
                "org_id": new_org.id,
                "org_name": new_org.company_name,
                "business_number": org_in.business_registration_number
            }
        )
        
        # 5. 최종 트랜잭션 커밋(조직 + 역할 + 로그 일괄 확정)
        db.commit()
        
        return new_org

create_organization_policy = CreateOrganizationPolicy()
