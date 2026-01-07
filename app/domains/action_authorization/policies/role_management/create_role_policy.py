from sqlalchemy.orm import Session
from typing import Optional

from app.core.exceptions import ForbiddenError
from app.models.objects.user import User
from app.domains.inter_domain.role_management.schemas.role_command import RoleCreate

class CreateRolePolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_in: RoleCreate,
        x_organization_id: Optional[int]
    ) -> None:
        """
        역할 생성을 위한 정책을 실행합니다.
        - 보호된 시스템 역할 생성을 방지합니다.
        - API를 통한 보호된 tier(0, 1) 역할 생성을 방지합니다.
        """
        # 규칙 1: 보호된 tier (0, 1) 역할 생성 금지
        if role_in.tier is not None and role_in.tier < 2:
            raise ForbiddenError("Roles with a tier level below 2 cannot be created via the API.")

        # 규칙 2: 보호된 시스템 역할 이름 생성 금지 (이중 방어)
        protected_system_roles = ["SUPER_ADMIN", "System_Admin", "Prime_Admin", "Admin"]
        if role_in.name in protected_system_roles and role_in.scope == "SYSTEM":
            raise ForbiddenError("Creation of system-level administrative roles is not allowed via API.")
        
        # 규칙 3: 조직 스코프 역할 생성 시, organization_id가 제공되어야 함
        if role_in.scope == "ORGANIZATION" and x_organization_id is None:
            raise ForbiddenError("Organization-scoped roles must be created within an organization context.")

        # 규칙 4: 조직 스코프 역할 생성 시, 요청자가 해당 조직의 관리 권한을 가져야 함
        #    (이 부분은 PermissionChecker("role:create", organization_id=x_organization_id)를 통해 암묵적으로 처리될 수 있음)
        #    여기서는 단순히 organization_id가 제공되었다고 가정하고, PermissionChecker가 충분히 검증했다고 가정

create_role_policy = CreateRolePolicy()
