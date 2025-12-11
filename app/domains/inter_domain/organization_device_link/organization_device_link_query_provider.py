from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.organization_device_link.services.organization_device_link_query_service import organization_device_link_query_service
from app.domains.services.organization_device_link.schemas.organization_device_link_query import OrganizationDeviceLinkRead

class OrganizationDeviceLinkQueryProvider:
    def get_link_by_ids(
        self, db: Session, *, organization_id: int, device_id: int, relationship_type: str
    ) -> Optional[OrganizationDeviceLinkRead]:
        return organization_device_link_query_service.get_link_by_ids(
            db, organization_id=organization_id, device_id=device_id, relationship_type=relationship_type
        )

    def get_all_links_for_organization(
        self, db: Session, *, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrganizationDeviceLinkRead]:
        return organization_device_link_query_service.get_all_links_for_organization(db, organization_id=organization_id, skip=skip, limit=limit)

    def get_all_links_for_device(
        self, db: Session, *, device_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrganizationDeviceLinkRead]:
        return organization_device_link_query_service.get_all_links_for_device(db, device_id=device_id, skip=skip, limit=limit)

organization_device_link_query_provider = OrganizationDeviceLinkQueryProvider()
