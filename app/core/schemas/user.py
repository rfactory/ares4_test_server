from pydantic import BaseModel, Field
from typing import List, Optional

class UserRolesUpdate(BaseModel):
    assign_role_ids: Optional[List[int]] = []
    revoke_role_ids: Optional[List[int]] = []

class SwitchContextRequest(BaseModel):
    target_organization_id: int = Field(..., description="전환하려는 대상 조직의 ID")
