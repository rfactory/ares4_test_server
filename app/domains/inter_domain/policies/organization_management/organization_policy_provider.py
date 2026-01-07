from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationCreate
from app.domains.action_authorization.policies.organization_management.create_organization_policy import create_organization_policy

class OrganizationPolicyProvider:
    """
    Organization Management Policy에 대한 공개 인터페이스입니다.
    외부 도메인은 이 Provider를 통해서만 조직 관리 정책에 접근해야 합니다.
    """
    def create_organization(
        self, 
        db: Session, 
        *, 
        org_in: OrganizationCreate, 
        actor_user: User
    ) -> Organization:
        """
        새로운 조직을 생성하는 정책을 실행합니다.
        """
        return create_organization_policy.execute(
            db, org_in=org_in, actor_user=actor_user
        )

organization_policy_provider = OrganizationPolicyProvider()