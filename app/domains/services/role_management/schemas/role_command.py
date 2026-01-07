from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from .role_query import RoleBase

class RoleCreate(RoleBase):
    organization_id: Optional[int] = None
    tier: int = 2
    max_headcount: Optional[int] = None

# 부분 수정을 허용하기 위해 모든 필드를 Optional로 정의
class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[int] = None

class PermissionAssignment(BaseModel):
    permission_id: int
    allowed_columns: Optional[List[str]] = None
    filter_condition: Optional[Dict[str, Any]] = None

class RolePermissionUpdateRequest(BaseModel):
    permissions: List[PermissionAssignment]
