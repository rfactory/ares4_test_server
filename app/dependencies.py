from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from jose import JWTError
from typing import Tuple, Optional
import copy # for deepcopy

from app.database import SessionLocal
from app.core import security
from app.core.redis_client import get_redis_client
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.models.objects.user import User as DBUser
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.models.objects.role import Role
from app.models.relationships.role_permission import RolePermission
from app.models.objects.permission import Permission
from app.models.objects.organization import Organization

from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.governance.governance_command_provider import governance_command_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider # 역할 조회를 위해 추가
from app.domains.inter_domain.permissions.permission_query_provider import permission_query_provider # 권한 조회를 위해 추가

import redis
from app.core.config import get_settings

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
    현재 사용자를 가져옵니다. 이때, DPoP 헤더를 검증하고, 사용자의 역할 할당 및 권한 정보를 미리 로드합니다.
    JKT(DPoP Key Thumbprint)를 함께 반환하여 중복 검증을 방지합니다.
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

class PermissionChecker:
    """
    요청된 권한이 있는지 확인하고, 임시 관리자 컨텍스트 및 비상 모드를 처리하는 의존성 클래스입니다.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        request: Request,
        db: Session = Depends(get_db),
        user_info: Tuple[DBUser, str, Optional[str]] = Depends(get_current_user)
    ):
        current_user, token, dpop_jkt = user_info
        
        # 헤더에서 'X-Organization-ID' 값을 직접 읽어옵니다.
        header_org_id_str = request.headers.get("X-Organization-ID")
        header_org_id = int(header_org_id_str) if header_org_id_str and header_org_id_str.isdigit() else None
        
        effective_org_id = header_org_id
        user_to_check = current_user

        # JWT에서 temp_org_id 클레임 확인 (컨텍스트 전환 시나리오)
        try:
            # dpop_jkt는 get_current_user에서 이미 검증되었으므로 여기서는 인자로 전달
            payload = security.decode_access_token(token, dpop_jkt=dpop_jkt)
            temp_org_id = payload.get("temp_org_id")
            
            is_system_scope_user = any(a.role.scope == 'SYSTEM' for a in current_user.user_role_assignments)

            if temp_org_id and is_system_scope_user:
                if temp_org_id == header_org_id:
                    # system:context_switch 권한이 있는지 확인
                    user_permissions = permission_query_provider.get_permissions_for_user_in_context(
                        db, user_id=current_user.id, organization_id=None
                    )
                    
                    if "system:context_switch" not in user_permissions:
                        raise security.HTTPException(status.HTTP_403_FORBIDDEN, detail="User lacks system:context_switch permission")
                    
                    # 유효한 임시 컨텍스트이므로 effective_org_id를 임시 ID로 설정
                    effective_org_id = temp_org_id
                else:
                    # 토큰의 임시 컨텍스트와 헤더의 조직 ID가 다르면 에러
                    raise security.HTTPException(status.HTTP_403_FORBIDDEN, detail="Token's temporary context does not match X-Organization-ID header")

        except (JWTError, security.HTTPException):
            # 토큰이 유효하지 않거나 DPoP 검증 실패 시, get_current_user에서 이미 처리됨. 여기서는 클레임 관련 에러만 처리.
            pass
        
        # 비상 모드 처리 (기존 로직)
        redis_client = get_redis_client()
        is_emergency_mode = redis_client.get(governance_command_provider.EMERGENCY_MODE_KEY)
        
        if is_emergency_mode:
            is_system_admin = any(
                assignment.role.name == "System_Admin" for assignment in current_user.user_role_assignments
            )
            if is_system_admin:
                prime_admin_role = role_query_provider.get_role_by_name(db, name="Prime_Admin")
                if prime_admin_role:
                    user_to_check = copy.deepcopy(current_user)
                    temp_assignment = UserOrganizationRole(role=prime_admin_role, user_id=user_to_check.id)
                    user_to_check.user_role_assignments.append(temp_assignment)

        # 최종 결정된 effective_org_id로 권한 검증
        permission_validator_provider.validate(
            db,
            user=user_to_check,
            permission_name=self.required_permission,
            organization_id=effective_org_id
        )