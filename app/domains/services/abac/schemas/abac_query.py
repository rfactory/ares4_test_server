from pydantic import BaseModel
from typing import Optional

class AbacVariableBase(BaseModel):
    name: str
    description: Optional[str] = None

class AbacVariableResponse(AbacVariableBase):
    class Config:
        from_attributes = True
