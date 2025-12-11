from sqlalchemy.orm import Session

from app.core.crud_base import CRUDBase
from app.models.relationships.organization_device import OrganizationDevice
from ..schemas.organization_device_link_command import OrganizationDeviceLinkCreate, OrganizationDeviceLinkUpdate

class CRUDOrganizationDeviceLinkCommand(CRUDBase[OrganizationDevice, OrganizationDeviceLinkCreate, OrganizationDeviceLinkUpdate]):
    def remove(self, db: Session, *, id: int) -> OrganizationDevice:
        """조직-장치 연결을 soft-delete 처리합니다."""
        obj = db.query(self.model).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
        return obj

organization_device_link_command_crud = CRUDOrganizationDeviceLinkCommand(OrganizationDevice)
