# file: server2/app/domains/inter_domain/user_identity/schemas/user_identity_command.py
"""
이 파일은 user_identity 도메인의 'command' 관련 Pydantic 스키마를 다른 도메인에 안전하게 노출(re-export)합니다.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
# Re-exporting from the service layer schema
from ....services.user_identity.schemas.user_identity_command import UserCreate, UserUpdate, RoleIdRequest

class CompleteRegistration(BaseModel):
    email: EmailStr
    verification_code: str

class ContextSwitchRequest(BaseModel):
    organization_id: int
