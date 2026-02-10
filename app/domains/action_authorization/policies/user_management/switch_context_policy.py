from typing import Optional
from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.organization import Organization
from app.core.exceptions import NotFoundError
from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class SwitchContextPolicy:
    def switch_to_organization_context(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_organization_id: int
    ) -> Organization:
        """시스템 관리자가 특정 조직의 컨텍스트로 전환합니다."""
        
        # 1. 권한 검증
        permission_validator_provider.validate(
            db, 
            user=actor_user, 
            permission_name="system:context_switch",
            organization_id=None 
        )

        # 2. 대상 조직 조회
        target_organization: Optional[Organization] = organization_query_provider.get_organization_by_id(
            db, 
            org_id=target_organization_id
        )

        if not target_organization:
            raise NotFoundError(f"Organization with ID {target_organization_id} not found.")
        
        # [Ares Aegis] 3. 감사 로그 기록
        # 이 기록은 나중에 관리자의 오남용을 감시하는 핵심 증거가 됩니다.
        audit_command_provider.log(
            db=db,
            event_type="CONTEXT_SWITCHED",
            description=f"Admin {actor_user.username} switched context to Org: {target_organization.company_name}",
            actor_user=actor_user,
            details={
                "target_org_id": target_organization_id,
                "target_org_name": target_organization.company_name,
                "reason": "Administrative access"
            }
        )

        # 4. 최종 트랜잭션 커밋 (로그 기록 확정)
        db.commit()

        # 5. 임시 역할 할당 또는 세션 관리 로직 (To-Do 가이드)
        # 이 Policy를 호출한 Service 계층에서는 이제 반환된 target_organization을 바탕으로
        # 새로운 Claims이 담긴 JWT를 발급하거나 Redis 세션을 갱신하게 됩니다.

        return target_organization

switch_context_policy = SwitchContextPolicy()