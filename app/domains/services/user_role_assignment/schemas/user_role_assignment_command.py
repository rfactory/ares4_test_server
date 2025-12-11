# --- Command-related Schemas ---
from pydantic import BaseModel
from typing import Optional

class UserRoleAssignmentCreate(BaseModel):
    user_id: int
    role_id: int
    organization_id: Optional[int] = None
