# --- Query-related Schemas ---
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Basic schemas for nested objects to avoid circular imports
# In a real scenario, these might be imported from their respective domains
class UserRead(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class RoleRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class UserRoleAssignmentRead(BaseModel):
    id: int
    user_id: int
    role_id: int
    organization_id: Optional[int] = None
    created_at: datetime

    user: UserRead
    role: RoleRead

    class Config:
        from_attributes = True
