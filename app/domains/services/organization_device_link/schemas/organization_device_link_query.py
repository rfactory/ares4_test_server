from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- Enums ---
class RelationshipType(str, Enum):
    OWNER = "OWNER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

class OrganizationDeviceLinkBase(BaseModel):
    organization_id: int
    device_id: int
    relationship_type: RelationshipType # 관계 유형

class OrganizationDeviceLinkRead(OrganizationDeviceLinkBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
