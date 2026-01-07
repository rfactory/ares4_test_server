from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str # 역할의 범위를 나타내는 필드 추가

class RoleResponse(RoleBase):
    id: int
    max_headcount: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class RolePermissionResponse(BaseModel):
    id: int
    role_id: int
    permission_id: int
    permission_name: str
    permission_description: Optional[str] = None
    allowed_columns: Optional[List[str]] = None
    filter_condition: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
