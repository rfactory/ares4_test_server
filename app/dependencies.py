from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from jose import JWTError
from typing import Tuple, Optional
import copy 
from pydantic import BaseModel, ConfigDict

from app.database import SessionLocal
from app.core import security
from app.core.redis_client import get_redis_client
from app.models.objects.user import User as DBUser
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.models.objects.role import Role
from app.models.relationships.role_permission import RolePermission
from app.models.objects.permission import Permission
from app.models.objects.organization import Organization

from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.governance.governance_command_provider import governance_command_provider
from app.domains.inter_domain.permissions.permission_query_provider import permission_query_provider 
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider 
from app.domains.inter_domain.permissions.permission_query_provider import permission_query_provider

# [추가] ActiveContext 정의
class ActiveContext(BaseModel):
    user: DBUser
    org_id: Optional[int] = None
    type: str  # "SYSTEM_ADMINISTRATOR", "ORGANIZATION_MEMBER", "EMERGENCY_ADMIN" 등

    # Pydantic v2 설정 (SQLAlchemy 객체 허용)
    model_config = ConfigDict(arbitrary_types_allowed=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    request: Request, 
    db: Session = Depends(get_db), 
    token: str = Depends(security.extract_token_from_request)
) -> Tuple[DBUser, str, Optional[str]]:
    """
    현재 사용자를 가져옵니다. DPoP 헤더 검증 및 사용자 정보 로드.
    """
    try:
        dpop_jkt = await security.verify_dpop_proof(request, access_token=token)
        token_data = security.verify_access_token(token, dpop_jkt=dpop_jkt)
        if token_data is None or token_data.id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token data")

    except HTTPException as e:
        new_nonce = security.generate_dpop_nonce()
        e.headers = e.headers or {}
        e.headers["WWW-Authenticate"] = "DPoP"
        e.headers["DPoP-Nonce"] = new_nonce
        raise e
    except JWTError:
        new_nonce = security.generate_dpop_nonce()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": new_nonce},
        )
    
    user = db.query(DBUser).options(
        joinedload(DBUser.user_role_assignments).joinedload(UserOrganizationRole.role).joinedload(Role.permissions).joinedload(RolePermission.permission),
        joinedload(DBUser.user_role_assignments).joinedload(UserOrganizationRole.organization)
    ).filter(DBUser.id == token_data.id).first()

    if not user:
        new_nonce = security.generate_dpop_nonce()
        raise HTTPException(status_code=404, detail="User not found", headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": new_nonce})
    return user, token, dpop_jkt

# [핵심] 기존 PermissionChecker의 로직을 추출하여 get_active_context 구현
async def get_active_context(
    request: Request,
    db: Session = Depends(get_db),
    user_info: Tuple[DBUser, str, Optional[str]] = Depends(get_current_user)
) -> ActiveContext:
    """
    현재 요청의 컨텍스트(조직, 시스템, 비상 모드 등)를 결정하고 ActiveContext 객체를 반환합니다.
    """
    current_user, token, dpop_jkt = user_info
    
    # 1. 헤더에서 조직 ID 추출
    header_org_id_str = request.headers.get("X-Organization-ID")
    header_org_id = int(header_org_id_str) if header_org_id_str and header_org_id_str.isdigit() else None
    
    effective_org_id = header_org_id
    user_to_check = current_user
    context_type = "ORGANIZATION_MEMBER" # 기본값

    # 2. JWT temp_org_id (컨텍스트 스위칭) 확인
    try:
        payload = security.decode_access_token(token, dpop_jkt=dpop_jkt)
        temp_org_id = payload.get("temp_org_id")
        
        is_system_scope_user = any(a.role.scope == 'SYSTEM' for a in current_user.user_role_assignments)

        if temp_org_id and is_system_scope_user:
            if temp_org_id == header_org_id:
                # system:context_switch 권한 확인
                user_permissions = permission_query_provider.get_permissions_for_user_in_context(
                    db, user_id=current_user.id, organization_id=None
                )
                
                if "system:context_switch" not in user_permissions:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="User lacks system:context_switch permission")
                
                effective_org_id = temp_org_id
            else:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Token's temporary context does not match X-Organization-ID header")

    except (JWTError, HTTPException):
        # 토큰 검증 실패는 get_current_user에서 처리되므로 여기서는 무시하거나 pass
        pass
    
    # 3. 비상 모드 처리 (Redis)
    redis_client = get_redis_client()
    is_emergency_mode = redis_client.get(governance_command_provider.EMERGENCY_MODE_KEY)
    
    if is_emergency_mode:
        is_system_admin = any(
            assignment.role.name == "System_Admin" for assignment in current_user.user_role_assignments
        )
        if is_system_admin:
            prime_admin_role = role_query_provider.get_role_by_name(db, name="Prime_Admin")
            if prime_admin_role:
                # 사용자 객체를 복사하여 임시 권한 부여
                user_to_check = copy.deepcopy(current_user)
                temp_assignment = UserOrganizationRole(role=prime_admin_role, user_id=user_to_check.id)
                user_to_check.user_role_assignments.append(temp_assignment)
                context_type = "EMERGENCY_ADMIN"

    # 4. 시스템 관리자 컨텍스트 판별
    # effective_org_id가 없고, 사용자가 SYSTEM 스코프 역할을 가진 경우
    if effective_org_id is None:
        is_system_user = any(a.role.scope == 'SYSTEM' for a in user_to_check.user_role_assignments)
        if is_system_user:
            context_type = "SYSTEM_ADMINISTRATOR"

    return ActiveContext(
        user=user_to_check,
        org_id=effective_org_id,
        type=context_type
    )

class PermissionChecker:
    """
    get_active_context를 의존성으로 받아 권한을 검증합니다.
    로직이 훨씬 간결해집니다.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        db: Session = Depends(get_db),
        active_context: ActiveContext = Depends(get_active_context)
    ):
        # ActiveContext에서 결정된 사용자(user_to_check)와 조직(effective_org_id)을 사용
        permission_validator_provider.validate(
            db,
            user=active_context.user,
            permission_name=self.required_permission,
            organization_id=active_context.org_id
        )