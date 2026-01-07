from sqlalchemy.orm import Session

from app.models.objects.organization import Organization
from app.models.objects.organization_type import OrganizationType
from app.models.objects.user import User
from app.domains.services.organizations.schemas.organization_command import OrganizationCreate, OrganizationUpdate
from app.domains.services.organizations.crud.organization_type_command_crud import OrganizationTypeCreate
from app.domains.services.organizations.services.organization_command_service import organization_command_service

class OrganizationCommandProvider:
    """
    Organization Command 서비스에 대한 공개 인터페이스입니다.
    """
    def find_or_create_organization_type(self, db: Session, *, name: str) -> OrganizationType:
        return organization_command_service.find_or_create_organization_type(db, name=name)

    def create_organization_type(self, db: Session, *, org_type_in: OrganizationTypeCreate) -> OrganizationType:
        return organization_command_service.create_organization_type(db, org_type_in=org_type_in)

    def create_organization(self, db: Session, *, org_in: OrganizationCreate, actor_user: User) -> Organization:
        return organization_command_service.create_organization(db, org_in=org_in, actor_user=actor_user)

    def update_organization(self, db: Session, *, org_to_update: Organization, org_in: OrganizationUpdate, actor_user: User) -> Organization:
        return organization_command_service.update_organization(db, org_to_update=org_to_update, org_in=org_in, actor_user=actor_user)

    def delete_organization(self, db: Session, *, org_to_delete: Organization, actor_user: User) -> Organization:
        return organization_command_service.delete_organization(db, org_to_delete=org_to_delete, actor_user=actor_user)

organization_command_provider = OrganizationCommandProvider()
