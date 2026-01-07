from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from jose import JWTError
import copy # for deepcopy

from app.database import SessionLocal
from app.core import security
from app.core.redis_client import get_redis_client # 수정된 임포트
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

import redis
from app.core.config import get_settings

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> DBUser:
    """
    현재 사용자를 가져옵니다. 이때, 사용자의 역할 할당 및 권한 정보를 미리 로드합니다.
    """
    try:
        token_data = security.verify_access_token(token)
        if token_data is None or token_data.id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials, token data is invalid",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = db.query(DBUser).options(
        joinedload(DBUser.user_role_assignments).joinedload(UserOrganizationRole.role).joinedload(Role.permissions).joinedload(RolePermission.permission),
        joinedload(DBUser.user_role_assignments).joinedload(UserOrganizationRole.organization)
    ).filter(DBUser.id == token_data.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class PermissionChecker:
    """
    요청된 권한이 있는지 확인하고, 비상 모드 시 권한 위임을 처리하는 의존성 클래스입니다.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(
        self, 
        request: Request, 
        db: Session = Depends(get_db), 
        current_user: DBUser = Depends(get_current_user)
    ):
        organization_id = request.path_params.get("organization_id")
        org_id_int = int(organization_id) if organization_id and organization_id.isdigit() else None

        user_to_check = current_user

        # 1. 비상 모드 확인
        redis_client = get_redis_client()
        is_emergency_mode = redis_client.get(governance_command_provider.EMERGENCY_MODE_KEY)
        
        if is_emergency_mode:
            # 2. 사용자가 System_Admin인지 확인
            is_system_admin = any(
                assignment.role.name == "System_Admin" for assignment in current_user.user_role_assignments
            )
            if is_system_admin:
                # 3. Prime_Admin 역할의 권한을 임시로 부여
                prime_admin_role = role_query_provider.get_role_by_name(db, name="Prime_Admin")
                if prime_admin_role:
                    # 사용자의 권한 목록을 직접 수정하지 않기 위해 깊은 복사
                    user_to_check = copy.deepcopy(current_user)
                    # Prime_Admin 역할 할당을 임시로 추가
                    temp_assignment = UserOrganizationRole(role=prime_admin_role, user_id=user_to_check.id)
                    user_to_check.user_role_assignments.append(temp_assignment)

        # 4. 최종 권한 확인 (새로운 Validator 사용, 실패 시 여기서 바로 에러 발생)
        permission_validator_provider.validate(
            db, 
            user=user_to_check, # 수정되었거나 원래의 사용자 객체
            permission_name=self.required_permission,
            organization_id=org_id_int
        )