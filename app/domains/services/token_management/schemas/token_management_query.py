from pydantic import BaseModel
from typing import Optional

class TokenPayload(BaseModel):
    id: int
    temp_org_id: Optional[int] = None