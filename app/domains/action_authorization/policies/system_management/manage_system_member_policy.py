from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.core.exceptions import NotFoundError, ForbiddenError

# Inter-Domain Providers
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.validators.governance.governance_validator_provider import governance_validator_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.user_role_assignment.user_organization_role_command_provider import user_organization_role_command_provider
from app.domains.services.user_identity.schemas.user_identity_command import UserRoleAssignmentCreate
from app.domains.inter_domain.validators.object_existence.object_existence_validator_provider import object_existence_validator_provider

class ManageSystemMemberPolicy:
    """
    [Policy] 시스템 컨텍스트에서 멤버의 역할을 관리하는 로직을 오케스트레이션합니다.
    """
    def remove(self, db: Session, *, actor_user: User, user_to_remove_id: int):
        """시스템 멤버를 제거(역할 해제)합니다."""
        # 1. 데이터 조회 및 존재 여부 검증
        user_to_remove = user_identity_query_provider.get_user(db, user_id=user_to_remove_id)
        object_existence_validator_provider.validate(obj=user_to_remove, obj_name="User to remove", identifier=str(user_to_remove_id), should_exist=True)

        assignment_to_revoke = user_role_assignment_query_provider.get_assignment_for_user_in_context(db, user_id=user_to_remove.id, organization_id=None)
        object_existence_validator_provider.validate(obj=assignment_to_revoke, obj_name="Role assignment", identifier=f"user: {user_to_remove_id} in system context", should_exist=True)
        role_to_revoke = assignment_to_revoke.role

        # 2. 거버넌스 규칙 검증
        matching_rules = governance_query_provider.get_matching_rules(
            db, actor_user=actor_user, action="revoke_role", context=role_to_revoke.scope, target_role=role_to_revoke
        )
        prime_admin_count = governance_query_provider.get_prime_admin_count(db)
        governance_validator_provider.evaluate_rule(
            actor_user=actor_user, matching_rules=matching_rules, target_role=role_to_revoke, prime_admin_count=prime_admin_count
        )

        # 3. 최종 실행
        user_organization_role_command_provider.delete_by_context(db, user_id=user_to_remove_id, organization_id=None)
        db.commit()

    async def update_role(self, db: Session, *, actor_user: User, target_user_id: int, new_role_id: int):
        """시스템 멤버의 역할을 업데이트합니다. 기존 할당을 모두 삭제하고 새로 생성하여 데이터 무결성을 보장합니다."""
        # 1. 대상 유저, 새로운 역할 정보 조회 및 검증
        target_user = user_identity_query_provider.get_user(db, user_id=target_user_id)
        if not target_user:
            raise NotFoundError(f"Target user with id {target_user_id} not found.")

        new_role = role_query_provider.get_role(db, role_id=new_role_id)
        if not new_role or new_role.scope != 'SYSTEM':
            raise NotFoundError(f"System role with id {new_role_id} not found.")

        # 2. 거버넌스 규칙 검증 (핵심 보안 로직)
        matching_rules = governance_query_provider.get_matching_rules(
            db, actor_user=actor_user, action="assign_role", context='SYSTEM', target_role=new_role
        )
        current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=new_role.id)
        prime_admin_count = governance_query_provider.get_prime_admin_count(db)

        governance_validator_provider.evaluate_rule(
            actor_user=actor_user,
            matching_rules=matching_rules,
            target_role=new_role,
            current_headcount=current_headcount,
            prime_admin_count=prime_admin_count
        )

        # 3. 역할 업데이트: 전부 삭제 후 새로 생성
        user_organization_role_command_provider.delete_by_context(
            db, user_id=target_user_id, organization_id=None # System context
        )
        create_schema = UserRoleAssignmentCreate(user_id=target_user_id, role_id=new_role_id, organization_id=None)
        new_assignment = user_organization_role_command_provider.create(db, obj_in=create_schema)
        
        db.commit()
        return new_assignment

manage_system_member_policy = ManageSystemMemberPolicy()