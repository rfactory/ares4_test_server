from pydantic import BaseModel, EmailStr

class RegistrationDataResponse(BaseModel):
    email: EmailStr
    username: str
    hashed_password: str
