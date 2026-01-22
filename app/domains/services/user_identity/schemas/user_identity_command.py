from pydantic import BaseModel, EmailStr
from typing import Optional
from .user_identity_query import UserBase

class UserCreate(UserBase):
    password: str
    is_two_factor_enabled: Optional[bool] = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_two_factor_enabled: Optional[bool] = None

class RoleIdRequest(BaseModel):
    role_id: int

class UserRoleAssignmentCreate(BaseModel):
    user_id: int
    role_id: int
    organization_id: Optional[int] = None

class UserRoleAssignmentUpdate(BaseModel):
    role_id: int
