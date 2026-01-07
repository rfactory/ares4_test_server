from pydantic import BaseModel, EmailStr

class CacheRegistrationData(BaseModel):
    email: EmailStr
    username: str
    hashed_password: str
