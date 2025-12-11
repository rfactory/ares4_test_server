from pydantic import BaseModel, ConfigDict
from typing import Optional

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    max_headcount: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
