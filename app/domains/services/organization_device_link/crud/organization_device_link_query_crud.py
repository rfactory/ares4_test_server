from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.crud_base import CRUDBase
from app.models.relationships.organization_device import OrganizationDevice
from ..schemas.organization_device_link_command import OrganizationDeviceLinkCreate, OrganizationDeviceLinkUpdate

class CRUDOrganizationDeviceLinkQuery(CRUDBase[OrganizationDevice, OrganizationDeviceLinkCreate, OrganizationDeviceLinkUpdate]):
    def get_by_organization_id_and_device_id_and_relationship_type(
        self, db: Session, *, organization_id: int, device_id: int, relationship_type: str
    ) -> Optional[OrganizationDevice]:
        return db.query(OrganizationDevice).filter(
            OrganizationDevice.organization_id == organization_id,
            OrganizationDevice.device_id == device_id,
            OrganizationDevice.relationship_type == relationship_type
        ).first()

    def get_all_by_organization_id(self, db: Session, *, organization_id: int) -> List[OrganizationDevice]:
        return db.query(OrganizationDevice).filter(OrganizationDevice.organization_id == organization_id).all()

    def get_all_by_device_id(self, db: Session, *, device_id: int) -> List[OrganizationDevice]:
        return db.query(OrganizationDevice).filter(OrganizationDevice.device_id == device_id).all()

organization_device_link_query_crud = CRUDOrganizationDeviceLinkQuery(OrganizationDevice)
