from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr
# RequestTypeEnum is no longer needed as all requests are for existing users now.

# --- AccessRequest Schemas ---

class AccessRequestBase(BaseModel):
    email: EmailStr # Email of the user for whom the request is made (could be existing or new)
    requested_role_id: int
    reason: Optional[str] = None
    organization_id: Optional[int] = None # To link the request to an organization if it's an enterprise request

class AccessRequestCreate(AccessRequestBase):
    # This request is always for an *existing* user who has already been created (even if inactive).
    # The user_id will be derived from the user associated with this email.
    pass

class AccessRequestUpdate(BaseModel):
    # For admins to approve or reject
    status: str # e.g., 'approved', 'rejected'
    rejection_reason: Optional[str] = None

class AccessRequestResponse(AccessRequestBase):
    id: int
    user_id: int # Now non-optional as per the model
    status: str
    reviewed_by_user_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime # Added from TimestampMixin

    class Config:
        from_attributes = True