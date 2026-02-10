import logging
from sqlalchemy.orm import Session
from pydantic import EmailStr, BaseModel, Field
from fastapi import Request
from typing import List, Dict

from app.core.exceptions import AuthenticationError
from app.core.security import verify_dpop_proof

# Providers
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.validators.password.password_validator_provider import password_validator_provider
from app.domains.inter_domain.token_management.token_management_command_provider import token_management_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class UserPermissions(BaseModel):
    system: List[str] = Field(default_factory=list)
    organizations: Dict[str, List[str]] = Field(default_factory=dict)

class LoginPolicy:
    async def execute(self, db: Session, *, email: EmailStr, password: str, request: Request) -> dict:
        # 1. 사용자 조회
        user = user_identity_query_provider.get_user_by_email(db, email=email)

        # 2. 비밀번호 검증
        try:
            password_validator_provider.validate_password(password=password, user=user)
        except AuthenticationError as e:
            # 로그인 실패 시 감사 로그 기록
            if user: 
                audit_command_provider.log(
                    db=db,
                    event_type="USER_LOGIN_FAILED",
                    description=f"Failed login attempt for user: {user.username}",
                    actor_user=user,
                    target_user=user,
                    details={"email_attempted": email}
                )
            raise e

        # 3. DPoP 헤더 검증 및 jkt 추출
        dpop_jkt = await verify_dpop_proof(request, access_token=None)

        # 4. 토큰 쌍 발급 (jkt 포함)
        token_pair = token_management_command_provider.issue_token_pair(db=db, user=user, dpop_jkt=dpop_jkt)

        # 5. Pydantic 모델을 사용하여 구조화된 권한 정보 구성
        perms_model = UserPermissions()

        for assignment in user.user_role_assignments:
            role = assignment.role
            organization_id = assignment.organization_id
            permissions_for_role = [rp.permission.name for rp in role.permissions]

            if role.scope == 'SYSTEM':
                for perm_name in permissions_for_role:
                    # Pydantic 덕분에 perms_model.system이 List[str]임을 인지함 -> Any 사라짐
                    if perm_name not in perms_model.system:
                        perms_model.system.append(perm_name)
            
            elif role.scope == 'ORGANIZATION' and organization_id is not None:
                org_id_str = str(organization_id)
                
                # 키가 없으면 빈 리스트 생성 (Dict[str, List[str]] 타입 보장)
                if org_id_str not in perms_model.organizations:
                    perms_model.organizations[org_id_str] = []
                
                for perm_name in permissions_for_role:
                    if perm_name not in perms_model.organizations[org_id_str]:
                        perms_model.organizations[org_id_str].append(perm_name)

        # 6. user 객체를 딕셔너리로 변환 후 권한 정보 추가
        user_dict = user.as_dict()
        # [수정] model_dump()로 딕셔너리 변환
        user_dict["permissions"] = perms_model.model_dump()
        
        # 7. 최종 커밋
        db.commit()
        
        return {"user": user_dict, "token": token_pair}

login_policy = LoginPolicy()