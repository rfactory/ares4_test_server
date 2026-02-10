import logging
from sqlalchemy.orm import Session
from typing import Optional

from app.core.exceptions import ForbiddenError
from app.models.objects.user import User
from app.domains.inter_domain.role_management.schemas.role_command import RoleCreate
from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.role_management.role_command_provider import role_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

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
        Ares Aegis 최후의 보루로서 컨텍스트 무결성과 트랜잭션 원자성을 강제합니다.
        """
        try:
            # [규칙 1] 보호된 tier (0, 1) 역할 생성 방지
            if role_in.tier is not None and role_in.tier < 2:
                raise ForbiddenError("Roles with a tier level below 2 cannot be created via the API.")

            # [규칙 2] 보호된 시스템 역할 이름 중복 생성 방지
            protected_system_roles = ["SUPER_ADMIN", "System_Admin", "Prime_Admin", "Admin"]
            if role_in.name in protected_system_roles and role_in.scope == "SYSTEM":
                raise ForbiddenError("Creation of system-level administrative roles is not allowed via API.")
            
            # [규칙 3 & 4] 조직 스코프 역할에 대한 엄격한 컨텍스트 검증
            if role_in.scope == "ORGANIZATION":
                if x_organization_id is None:
                    raise ForbiddenError("Organization-scoped roles must be created within an organization context.")

                if role_in.organization_id != x_organization_id:
                    raise ForbiddenError("The organization ID in the request does not match the current active context.")

                permission_validator_provider.validate_for_role_assignment(
                    db, user=actor_user, organization_id=x_organization_id
                )
            
            # 5. [Command 수행] 실제 역할 생성 명령 하달
            new_role = role_command_provider.create_role(db, role_in=role_in, actor_user=actor_user)
            
            # 6. [Ares Aegis] 감사 로그 기록 (수행 성공 시)
            audit_command_provider.log(
                db=db,
                event_type="ROLE_CREATED",
                description=f"Role '{new_role.name}' created by {actor_user.username}",
                actor_user=actor_user,
                details={
                    "role_id": new_role.id,
                    "tier": new_role.tier,
                    "scope": new_role.scope,
                    "org_id": x_organization_id
                }
            )

            # 7. 모든 작업 성공 시 최종 트랜잭션 커밋
            db.commit()
            return new_role

        except Exception as e:
            # [핵심] 검증 실패, 생성 실패, 로그 실패 등 어떤 상황에서도 롤백 수행
            db.rollback()
            logger.error(f"Aegis Policy Violation or System Error: {str(e)}")
            # 발생한 예외를 다시 던져 엔드포인트가 대응하게 함
            raise e

create_role_policy = CreateRolePolicy()