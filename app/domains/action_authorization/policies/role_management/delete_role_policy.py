from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, ConflictError
from app.models.objects.user import User
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider

class DeleteRolePolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_id: int
    ) -> None:
        """
        역할 삭제를 위한 정책을 실행합니다.
        - 보호된 역할(tier 0, 1) 삭제를 방지합니다.
        - 사용 중인 역할 삭제를 방지합니다.
        """
        target_role = role_query_provider.get_role(db, role_id=role_id)
        if not target_role:
            # 역할이 없는 경우는 API 계층의 NotFoundError로 이미 처리됨
            return

        # 규칙 1: 보호된 역할 (tier 0, 1) 삭제 금지
        if target_role.tier is not None and target_role.tier < 2:
            raise ForbiddenError(f"Protected role '{target_role.name}' (tier {target_role.tier}) cannot be deleted.")

        # 규칙 2: 사용 중인 역할 삭제 금지 (연결된 사용자가 있는지 확인)
        if target_role.users:
            raise ConflictError(f"Role '{target_role.name}' is currently assigned to user(s) and cannot be deleted.")

delete_role_policy = DeleteRolePolicy()
