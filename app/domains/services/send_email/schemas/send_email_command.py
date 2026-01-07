from pydantic import BaseModel, EmailStr
from typing import Dict, Any

class EmailSchema(BaseModel):
    to: EmailStr
    subject: str
    template_name: str
    context: Dict[str, Any]
