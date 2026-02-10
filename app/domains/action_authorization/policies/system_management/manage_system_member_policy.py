from sqlalchemy.orm import Session
import logging
from app.models.objects.user import User
from app.core.exceptions import NotFoundError, ForbiddenError, AppLogicError

# Inter-Domain Providers
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.validators.governance.governance_validator_provider import governance_validator_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.user_role_assignment.user_organization_role_command_provider import user_organization_role_command_provider
from app.domains.services.user_identity.schemas.user_identity_command import UserRoleAssignmentCreate
from app.domains.inter_domain.validators.object_existence.object_existence_validator_provider import object_existence_validator_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.validators.headcount.headcount_validator_provider import headcount_validator_provider

logger = logging.getLogger(__name__)

class ManageSystemMemberPolicy:
    """
    [지휘 계층] 시스템 멤버십 변경을 오케스트레이션하며 트랜잭션 원자성을 보장합니다.
    """

    def remove(self, db: Session, *, actor_user: User, user_to_remove_id: int):
        """시스템 멤버를 제거하며 트랜잭션을 완결합니다."""
        try:
            # 1. 데이터 조회 및 검증
            user_to_remove = user_identity_query_provider.get_user(db, user_id=user_to_remove_id)
            object_existence_validator_provider.validate(obj=user_to_remove, obj_name="User", identifier=str(user_to_remove_id), should_exist=True)

            assignment_to_revoke = user_role_assignment_query_provider.get_assignment_for_user_in_context(db, user_id=user_to_remove.id, organization_id=None)
            object_existence_validator_provider.validate(obj=assignment_to_revoke, obj_name="Role assignment", identifier="System Context", should_exist=True)
            
            role_to_revoke = assignment_to_revoke.role

            # 2. 거버넌스 규칙 검증 (Prime Admin 최소 인원 등)
            matching_rules = governance_query_provider.get_matching_rules(db, actor_user=actor_user, action="revoke_role", context='SYSTEM', target_role=role_to_revoke)
            prime_admin_count = governance_query_provider.get_prime_admin_count(db)
            governance_validator_provider.evaluate_rule(actor_user=actor_user, matching_rules=matching_rules, target_role=role_to_revoke, prime_admin_count=prime_admin_count)

            # 3. [수행] 역할 해제
            user_organization_role_command_provider.delete_by_context(db, user_id=user_to_remove_id, organization_id=None)

            # 4. [기록] 감사 로그
            audit_command_provider.log(
                db=db,
                event_type="SYSTEM_MEMBER_REMOVED",
                description=f"User {user_to_remove_id} removed from system by {actor_user.username}",
                actor_user=actor_user,
                details={"revoked_role": role_to_revoke.name}
            )

            # 5. [확정] 단 한 번의 커밋
            db.commit()
            logger.info(f"POLICY: System member {user_to_remove_id} removed and committed.")

        except Exception as e:
            db.rollback()
            logger.error(f"POLICY_ERROR: System member removal failed: {e}")
            raise e

    async def update_role(self, db: Session, *, actor_user: User, target_user_id: int, new_role_id: int):
        """시스템 멤버의 역할을 업데이트하며 트랜잭션을 완결합니다."""
        try:
            # 1. 데이터 조회 및 검증
            target_user = user_identity_query_provider.get_user(db, user_id=target_user_id)
            if not target_user:
                raise NotFoundError(f"User {target_user_id} not found.")

            new_role = role_query_provider.get_role(db, role_id=new_role_id)
            if not new_role or new_role.scope != 'SYSTEM':
                raise AppLogicError("Invalid system role.")

            current_assignment = user_role_assignment_query_provider.get_assignment_for_user_in_context(db, user_id=target_user_id, organization_id=None)
            old_role_name = current_assignment.role.name if current_assignment else "None"

            # 2. 거버넌스 및 정원 검증
            matching_rules = governance_query_provider.get_matching_rules(db, actor_user=actor_user, action="assign_role", context='SYSTEM', target_role=new_role)
            current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=new_role.id)
            prime_admin_count = governance_query_provider.get_prime_admin_count(db)

            governance_validator_provider.evaluate_rule(actor_user=actor_user, matching_rules=matching_rules, target_role=new_role, current_headcount=current_headcount, prime_admin_count=prime_admin_count)
            headcount_validator_provider.validate(role_name=new_role.name, current_headcount=current_headcount, max_headcount=new_role.max_headcount)

            # 3. [수행] 역할 교체
            user_organization_role_command_provider.delete_by_context(db, user_id=target_user_id, organization_id=None)
            create_schema = UserRoleAssignmentCreate(user_id=target_user_id, role_id=new_role_id, organization_id=None)
            new_assignment = user_organization_role_command_provider.create(db, obj_in=create_schema)
            
            # 4. [기록] 감사 로그
            audit_command_provider.log(
                db=db,
                event_type="SYSTEM_MEMBER_ROLE_UPDATED",
                description=f"System role updated for user {target_user_id}",
                actor_user=actor_user,
                details={"old_role": old_role_name, "new_role": new_role.name}
            )

            # 5. [확정] 커밋
            db.commit()
            db.refresh(new_assignment)
            return new_assignment

        except Exception as e:
            db.rollback()
            logger.error(f"POLICY_ERROR: System member role update failed: {e}")
            raise e

manage_system_member_policy = ManageSystemMemberPolicy()