# C:\vscode project files\Ares4\server2\app\domains\inter_domain\organization\organization_command_provider.py
from sqlalchemy.orm import Session

from app.models.objects.organization import Organization
from app.models.objects.user import User
from app.domains.services.organizations.schemas.organization_command import OrganizationCreate, OrganizationUpdate
from app.domains.services.organizations.services.organization_command_service import organization_command_service

class OrganizationCommandProvider:
    """
    Organization Command 서비스에 대한 공개 인터페이스입니다.
    외부 도메인은 이 Provider를 통해서만 데이터 변경 기능에 접근해야 합니다.
    """
    def create_organization(self, db: Session, *, org_in: OrganizationCreate, actor_user: User) -> Organization:
        return organization_command_service.create_organization(db, org_in=org_in, actor_user=actor_user)

    def update_organization(self, db: Session, *, org_id: int, org_in: OrganizationUpdate, actor_user: User) -> Organization:
        return organization_command_service.update_organization(db, org_id=org_id, org_in=org_in, actor_user=actor_user)

    def delete_organization(self, db: Session, *, org_id: int, actor_user: User) -> Organization:
        return organization_command_service.delete_organization(db, org_id=org_id, actor_user=actor_user)

organization_command_provider = OrganizationCommandProvider()
