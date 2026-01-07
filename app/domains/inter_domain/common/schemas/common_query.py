from typing import List, Optional
from pydantic import BaseModel

class ResourceColumn(BaseModel):
    name: str
    type: str # 예: 'string', 'integer', 'boolean', 'datetime'
    description: Optional[str] = None

class ManageableResourceResponse(BaseModel):
    resource_name: str # 리소스의 고유 이름 (예: 'organization', 'user')
    columns: List[ResourceColumn]
    description: Optional[str] = None

    class Config:
        from_attributes = True
