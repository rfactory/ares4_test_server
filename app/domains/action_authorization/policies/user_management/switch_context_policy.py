from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.core.exceptions import NotFoundError
from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider

class SwitchContextPolicy:
    def switch_to_organization_context(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_organization_id: int
    ) -> Organization:
        """시스템 관리자가 특정 조직의 컨텍스트로 전환합니다."""
        # 1. 시스템 관리자 역할이 'system:context_switch' 권한을 가지고 있는지 확인
        permission_validator_provider.validate(
            db, 
            user=actor_user, 
            permission_name="system:context_switch",
            organization_id=None # 시스템 컨텍스트의 권한이므로 organization_id는 None
        )

        # 2. 대상 조직 조회
        target_organization = organization_query_provider.get_organization_by_id(db, organization_id=target_organization_id)
        if not target_organization:
            raise NotFoundError(f"Organization with ID {target_organization_id} not found.")
        
        # 3. 임시 역할 할당 또는 세션 관리 로직 (To-Do)
        # 이 부분은 JWT 토큰에 임시 클레임을 추가하거나 Redis/DB에 임시 매핑을 저장하는 방식으로 구현될 수 있습니다.

        return target_organization

switch_context_policy = SwitchContextPolicy()

