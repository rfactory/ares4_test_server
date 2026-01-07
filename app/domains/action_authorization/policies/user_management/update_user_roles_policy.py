from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.objects.user import User
from app.models.objects.role import Role

# Import all necessary providers for orchestration
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.validators.governance.governance_validator_provider import governance_validator_provider
from app.domains.inter_domain.validators.last_org_admin.last_org_admin_validator_provider import last_org_admin_validator_provider
from app.domains.inter_domain.validators.headcount.headcount_validator_provider import headcount_validator_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_command_provider import user_role_assignment_command_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.governance.governance_command_provider import governance_command_provider
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider

class UpdateUserRolesPolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user_id: int, 
        target_user_id: int, 
        roles_to_assign: Optional[List[Role]] = None,
        roles_to_revoke: Optional[List[Role]] = None
    ) -> None:
        """
        사용자 역할 변경의 전체 워크플로우를 조율(Orchestrate)합니다.
        """
        # 1. 데이터 조회
        actor_user = user_identity_query_provider.get_user(db, user_id=actor_user_id)
        if not actor_user:
            raise NotFoundError(resource="Actor User", resource_id=str(actor_user_id))
        
        target_user = user_identity_query_provider.get_user(db, user_id=target_user_id)
        if not target_user:
            raise NotFoundError(resource="Target User", resource_id=str(target_user_id))

        roles_to_assign = roles_to_assign or []
        roles_to_revoke = roles_to_revoke or []

        # 2. 유효성 검사
        for role in roles_to_assign:
            # 2a. 데이터 수집
            matching_rules = governance_query_provider.get_matching_rules(
                db=db, actor_user=actor_user, action="assign_role", context=role.scope, target_role=role
            )
            current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=role.id)
            prime_admin_count = governance_query_provider.get_prime_admin_count(db)

            # 2b. 거버넌스 규칙 검증 (Validator가 실패 시 직접 에러 발생)
            governance_validator_provider.evaluate_rule(
                actor_user=actor_user,
                matching_rules=matching_rules,
                target_role=role,
                current_headcount=current_headcount,
                prime_admin_count=prime_admin_count
            )

            # 2c. 최대 인원수 확인 (별도 Validator가 실패 시 직접 에러 발생)
            headcount_validator_provider.validate(
                role_name=role.name,
                current_headcount=current_headcount,
                max_headcount=role.max_headcount
            )

        for role in roles_to_revoke:
            # 2d. 데이터 수집
            matching_rules = governance_query_provider.get_matching_rules(
                db=db, actor_user=actor_user, action="revoke_role", context=role.scope, target_role=role
            )
            prime_admin_count = governance_query_provider.get_prime_admin_count(db)

            # 2e. 거버넌스 규칙 검증
            governance_validator_provider.evaluate_rule(
                actor_user=actor_user,
                matching_rules=matching_rules,
                target_role=role,
                prime_admin_count=prime_admin_count
            )

        # 2f. 마지막 조직 관리자 이탈 방지
        last_org_admin_validator_provider.validate(
            db=db, target_user=target_user, roles_to_revoke=roles_to_revoke
        )

        # 3. 역할 할당/해제 실행
        user_role_assignment_command_provider.update_user_roles(
            db=db, target_user=target_user, roles_to_assign=roles_to_assign,
            roles_to_revoke=roles_to_revoke, actor_user=actor_user
        )

        # 4. 후속 조치 (비상 모드 확인)
        roles_changed = roles_to_assign + roles_to_revoke
        if roles_changed: # 역할 변경이 있었던 경우에만 실행
            governance_command_provider.check_and_update_emergency_mode(db, roles_changed=roles_changed)

        # 5. 트랜잭션 커밋
        db.commit()

update_user_roles_policy = UpdateUserRolesPolicy()
