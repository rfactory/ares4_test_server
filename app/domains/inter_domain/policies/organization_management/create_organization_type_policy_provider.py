from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationTypeCreate
# 실제 정책(Policy) 임포트
from app.domains.action_authorization.policies.organization_management.create_organization_type_policy import create_organization_type_policy

class CreateOrganizationTypePolicyProvider:
    """
    Organization Type 생성 정책에 대한 전용 인터페이스입니다.
    기존 organization_policy_provider와 분리하여 도메인 간 간섭을 최소화합니다.
    """
    def execute(
        self, 
        db: Session, 
        *, 
        org_type_in: OrganizationTypeCreate, 
        actor_user: User
    ):
        """
        새로운 조직 유형을 생성하는 정책을 실행합니다.
        (Ares Aegis: 정책 내부에서 감사 로그와 트랜잭션 완결)
        """
        return create_organization_type_policy.execute(
            db, org_type_in=org_type_in, actor_user=actor_user
        )

# 전역에서 사용할 싱글톤 인스턴스
create_organization_type_policy_provider = CreateOrganizationTypePolicyProvider()