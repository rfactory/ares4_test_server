from typing import Optional
from pydantic import BaseModel
from .organization_device_link_query import OrganizationDeviceLinkBase

class OrganizationDeviceLinkCreate(OrganizationDeviceLinkBase):
    pass

class OrganizationDeviceLinkUpdate(BaseModel):
    relationship_type: Optional[OrganizationDeviceLinkBase.RelationshipType] = None
    is_active: Optional[bool] = None
