from sqlalchemy.orm import Session

from app.domains.services.organization_device_link.services.organization_device_link_command_service import organization_device_link_command_service
from app.domains.services.organization_device_link.schemas.organization_device_link_command import OrganizationDeviceLinkCreate, OrganizationDeviceLinkUpdate
from app.models.relationships.organization_device import OrganizationDevice
from app.models.objects.user import User

class OrganizationDeviceLinkCommandProvider:
    def assign_device(
        self, db: Session, *, link_in: OrganizationDeviceLinkCreate, actor_user: User
    ) -> OrganizationDevice:
        return organization_device_link_command_service.assign_device(db, link_in=link_in, actor_user=actor_user)

    def unassign_device(self, db: Session, *, link_id: int, actor_user: User) -> OrganizationDevice:
        return organization_device_link_command_service.unassign_device(db, link_id=link_id, actor_user=actor_user)

    def update_assignment(
        self, db: Session, *, link_id: int, link_in: OrganizationDeviceLinkUpdate, actor_user: User
    ) -> OrganizationDevice:
        return organization_device_link_command_service.update_assignment(db, link_id=link_id, link_in=link_in, actor_user=actor_user)

organization_device_link_command_provider = OrganizationDeviceLinkCommandProvider()
