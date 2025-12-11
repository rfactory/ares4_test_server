from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.organization_device_link_query_crud import organization_device_link_query_crud
from ..schemas.organization_device_link_query import OrganizationDeviceLinkRead
from app.models.relationships.organization_device import OrganizationDevice

class OrganizationDeviceLinkQueryService:
    def get_link_by_ids(
        self, db: Session, *, organization_id: int, device_id: int, relationship_type: str
    ) -> Optional[OrganizationDeviceLinkRead]:
        db_link = organization_device_link_query_crud.get_by_organization_id_and_device_id_and_relationship_type(
            db, organization_id=organization_id, device_id=device_id, relationship_type=relationship_type
        )
        return OrganizationDeviceLinkRead.model_validate(db_link) if db_link else None

    def get_all_links_for_organization(
        self, db: Session, *, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrganizationDeviceLinkRead]:
        db_links = organization_device_link_query_crud.get_all_by_organization_id(db, organization_id=organization_id)
        return [OrganizationDeviceLinkRead.model_validate(link) for link in db_links]

    def get_all_links_for_device(
        self, db: Session, *, device_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrganizationDeviceLinkRead]:
        db_links = organization_device_link_query_crud.get_all_by_device_id(db, device_id=device_id)
        return [OrganizationDeviceLinkRead.model_validate(link) for link in db_links]

organization_device_link_query_service = OrganizationDeviceLinkQueryService()
