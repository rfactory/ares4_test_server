from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.models.objects.user import User
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.role_management.schemas.role_command import RoleUpdate

class UpdateRolePolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_id: int,
        role_in: RoleUpdate
    ) -> None:
        """
        역할 수정을 위한 정책을 실행합니다.
        - 보호된 역할(tier 0, 1)의 주요 속성(이름, 등급) 변경을 방지합니다.
        - 일반 역할을 보호된 등급으로 승격시키는 것을 방지합니다.
        """
        target_role = role_query_provider.get_role(db, role_id=role_id)
        if not target_role:
            return

        # 규칙 1: API를 통해 역할을 보호된 등급(tier 0 또는 1)으로 설정하려는 시도 차단
        if role_in.tier is not None and role_in.tier < 2:
            # 단, 원래 tier가 0 또는 1인 역할의 tier를 그대로 유지하려는 경우는 허용해야 하므로,
            # tier 값이 실제로 변경되는 경우에만 오류를 발생시킵니다.
            if role_in.tier != target_role.tier:
                raise ForbiddenError("Cannot set or change role tier to a protected level (0 or 1) via API.")

        # 규칙 2: 이미 보호된 역할(tier 0, 1)인 경우, 추가적인 변경 제한
        is_protected = target_role.tier is not None and target_role.tier < 2
        if is_protected:
            # 이름 변경 금지
            if role_in.name is not None and role_in.name != target_role.name:
                raise ForbiddenError(f"Name of protected role '{target_role.name}' (tier {target_role.tier}) cannot be changed.")
            
            # 등급 변경 금지 (규칙 1에서 일부 처리하지만, 명시적으로 한번 더 확인)
            if role_in.tier is not None and role_in.tier != target_role.tier:
                 raise ForbiddenError(f"Tier of protected role '{target_role.name}' cannot be changed.")

update_role_policy = UpdateRolePolicy()
