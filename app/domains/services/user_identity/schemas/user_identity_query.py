from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserInDBBase(UserBase):
    id: int
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    is_two_factor_enabled: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class User(UserInDBBase):
    pass

# --- Schemas for Token --- #

class Token(BaseModel):
    access_token: str
    token_type: str

class UserWithToken(BaseModel):
    user: User
    token: Token

# --- Member-related Schemas ---
class MemberResponse(BaseModel):
    """조직 구성원 정보를 반환하기 위한 스키마입니다."""
    id: int
    username: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)
