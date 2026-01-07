from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationCreate
from app.domains.action_authorization.policies.organization_management.create_organization_policy import create_organization_policy

class CreateOrganizationPolicyProvider:
    def execute(
        self, 
        db: Session, 
        *, 
        org_in: OrganizationCreate, 
        actor_user: User
    ) -> Organization:
        """
        조직 생성 및 관련 작업을 지휘하는 정책을 실행합니다.
        """
        return create_organization_policy.execute(
            db, org_in=org_in, actor_user=actor_user
        )

create_organization_policy_provider = CreateOrganizationPolicyProvider()
