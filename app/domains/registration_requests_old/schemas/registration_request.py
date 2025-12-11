from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr

# --- RegistrationRequest Schemas ---

class RegistrationRequestBase(BaseModel):
    username: str
    email: EmailStr

class RegistrationRequestCreate(RegistrationRequestBase):
    password: str
    requested_role_id: Optional[int] = None

class RegistrationRequestUpdate(BaseModel):
    status: str # approved, rejected
    rejection_reason: Optional[str] = None

class RegistrationRequestResponse(RegistrationRequestBase):
    id: int
    status: str
    requested_at: datetime
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    approved_by_user_id: Optional[int] = None
    requested_role_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
