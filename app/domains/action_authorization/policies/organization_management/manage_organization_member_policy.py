from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.models.objects.role import Role

# Inter-Domain Provider Imports
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.user_role_assignment.user_role_assignment_query_provider import user_role_assignment_query_provider
from app.domains.inter_domain.user_role_assignment.user_organization_role_command_provider import user_organization_role_command_provider
from app.domains.inter_domain.validators.permission.permission_validator_provider import permission_validator_provider
from app.domains.inter_domain.governance.governance_query_provider import governance_query_provider
from app.domains.inter_domain.validators.governance.governance_validator_provider import governance_validator_provider
from app.domains.inter_domain.validators.headcount.headcount_validator_provider import headcount_validator_provider
from app.domains.inter_domain.validators.object_existence.object_existence_validator_provider import object_existence_validator_provider
from app.domains.services.user_identity.schemas.user_identity_command import UserRoleAssignmentCreate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class ManageOrganizationMemberPolicy:
    """
    [Policy]
    구성원 역할 변경 및 제거 워크플로우를 관장하는 오케스트레이터입니다.
    """
    def remove(self, db: Session, *, actor_user: User, organization_id: int, user_to_remove_id: int):
        """구성원을 조직에서 제거(역할 해제)합니다."""
        # 1. 권한 검증
        permission_validator_provider.validate_for_role_assignment(db, user=actor_user, organization_id=organization_id)

        # 2. 데이터 조회 및 존재 여부 검증
        user_to_remove = user_identity_query_provider.get_user(db, user_id=user_to_remove_id)
        object_existence_validator_provider.validate(obj=user_to_remove, obj_name="User to remove", identifier=str(user_to_remove_id), should_exist=True)

        assignment_to_revoke = user_role_assignment_query_provider.get_assignment_for_user_in_context(db, user_id=user_to_remove.id, organization_id=organization_id)
        object_existence_validator_provider.validate(obj=assignment_to_revoke, obj_name="Role assignment", identifier=f"user: {user_to_remove_id} in org: {organization_id}", should_exist=True)
        role_to_revoke = assignment_to_revoke.role

        # 3. 거버넌스 규칙 검증
        matching_rules = governance_query_provider.get_matching_rules(
            db, actor_user=actor_user, action="revoke_role", context=role_to_revoke.scope, target_role=role_to_revoke
        )
        prime_admin_count = governance_query_provider.get_prime_admin_count(db)
        governance_validator_provider.evaluate_rule(
            actor_user=actor_user, matching_rules=matching_rules, target_role=role_to_revoke, prime_admin_count=prime_admin_count
        )

        # 4. 최종 실행
        user_organization_role_command_provider.delete_by_context(db, user_id=user_to_remove_id, organization_id=organization_id)
        
        # 5. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="ORG_MEMBER_REMOVED",
            description=f"User ID {user_to_remove_id} removed from Org {organization_id}",
            actor_user=actor_user,
            details={"target_user_id": user_to_remove_id, "org_id": organization_id}
        )
        
        # 6. 최종 트랜잭션 커밋
        db.commit()

    def update_role(self, db: Session, *, actor_user: User, organization_id: int, user_to_update_id: int, new_role_id: int):
        """구성원의 역할을 변경합니다. '전부 삭제 후 새로 생성' 로직을 사용합니다."""
        # 1. 권한 검증
        permission_validator_provider.validate_for_role_assignment(db, user=actor_user, organization_id=organization_id)

        # 2. 데이터 조회 및 존재 여부 검증
        user_to_update = user_identity_query_provider.get_user(db, user_id=user_to_update_id)
        object_existence_validator_provider.validate(obj=user_to_update, obj_name="User to update", identifier=str(user_to_update_id), should_exist=True)

        new_role = role_query_provider.get_role(db, role_id=new_role_id)
        object_existence_validator_provider.validate(obj=new_role, obj_name="New role", identifier=str(new_role_id), should_exist=True)

        # 3. 새 역할 할당 규칙 검증
        assign_rules = governance_query_provider.get_matching_rules(
            db, actor_user=actor_user, action="assign_role", context=new_role.scope, target_role=new_role
        )
        current_headcount = user_role_assignment_query_provider.get_user_count_for_role(db, role_id=new_role.id)
        prime_admin_count = governance_query_provider.get_prime_admin_count(db)
        governance_validator_provider.evaluate_rule(
            actor_user=actor_user, matching_rules=assign_rules, target_role=new_role, current_headcount=current_headcount, prime_admin_count=prime_admin_count
        )
        headcount_validator_provider.validate(
            role_name=new_role.name, current_headcount=current_headcount, max_headcount=new_role.max_headcount
        )

        # 4. 최종 실행: 전부 삭제 후 새로 생성
        user_organization_role_command_provider.delete_by_context(db, user_id=user_to_update_id, organization_id=organization_id)
        create_schema = UserRoleAssignmentCreate(user_id=user_to_update_id, role_id=new_role_id, organization_id=organization_id)
        user_organization_role_command_provider.create(db, obj_in=create_schema)
        
        # 5. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="ORG_MEMBER_ROLE_UPDATED",
            description=f"Role updated for User ID {user_to_update_id} in Org {organization_id}",
            actor_user=actor_user,
            details={
                "target_user_id": user_to_update_id,
                "new_role_id": new_role_id,
                "org_id": organization_id
            }
        )
        
        # 6. 최종 트랜잭션 커밋
        db.commit()

manage_organization_member_policy = ManageOrganizationMemberPolicy()