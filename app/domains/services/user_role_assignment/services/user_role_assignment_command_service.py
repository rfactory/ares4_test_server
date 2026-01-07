# --- Command-related Service ---
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.exceptions import NotFoundError
from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from ..crud.user_role_assignment_command_crud import user_role_assignment_crud_command
from ..schemas.user_role_assignment_command import UserRoleAssignmentCreate

class UserRoleAssignmentCommandService:

    def update_user_roles(
        self,
        db: Session,
        *,
        target_user: User,
        roles_to_assign: Optional[List[Role]] = None,
        roles_to_revoke: Optional[List[Role]] = None,
        actor_user: User,
    ) -> None:
        """
        사용자의 역할을 일괄적으로 업데이트합니다. (할당 및 해제)
        상위 Policy에서 모든 유효성 검사 및 후속 조치를 담당합니다.
        """
        roles_to_assign = roles_to_assign or []
        roles_to_revoke = roles_to_revoke or []

        for role in roles_to_revoke:
            self._internal_revoke_role(db, target_user=target_user, role=role, actor_user=actor_user)

        for role in roles_to_assign:
            self._internal_assign_role(db, target_user=target_user, role=role, actor_user=actor_user)

    def assign_role(
        self,
        db: Session,
        *,
        assignment_in: UserRoleAssignmentCreate,
        request_user: User,
    ) -> UserOrganizationRole:
        """
        사용자에게 단일 역할을 할당하는 공개 메소드입니다.
        상위 Policy에서 모든 유효성 검사 및 후속 조치를 담당합니다.
        """
        role = db.query(Role).filter(Role.id == assignment_in.role_id).first()
        if not role:
            raise NotFoundError("Role", str(assignment_in.role_id))
        
        user = db.query(User).filter(User.id == assignment_in.user_id).first()
        if not user:
            raise NotFoundError("User", str(assignment_in.user_id))

        return self._internal_assign_role(db, target_user=user, role=role, actor_user=request_user, organization_id=assignment_in.organization_id)

    def _internal_assign_role(
        self,
        db: Session,
        *,
        target_user: User,
        role: Role,
        actor_user: User,
        organization_id: Optional[int] = None
    ) -> UserOrganizationRole:
        """
        역할 할당의 핵심 내부 로직. 순수하게 할당만 실행합니다.
        """
        existing_assignment = user_role_assignment_crud_command.get_by_user_role_org(
            db, user_id=target_user.id, role_id=role.id, organization_id=organization_id
        )
        if existing_assignment:
            return existing_assignment

        assignment_schema = UserRoleAssignmentCreate(user_id=target_user.id, role_id=role.id, organization_id=organization_id)
        new_assignment = user_role_assignment_crud_command.create(db, obj_in=assignment_schema)
        
        audit_command_provider.log(
            db=db, 
            actor_user=actor_user, 
            event_type="USER_ROLE_ASSIGNED",
            description=f"Role '{role.name}' assigned to user '{target_user.username}'",
            details=new_assignment.as_dict()
        )
        return new_assignment

    def _internal_revoke_role(self, db: Session, *, target_user: User, role: Role, actor_user: User):
        """
        역할 해제의 핵심 내부 로직.
        """
        org_id = role.organization_id if role.scope == 'ORGANIZATION' else None

        assignment_to_delete = user_role_assignment_crud_command.get_by_user_role_org(
            db, user_id=target_user.id, role_id=role.id, organization_id=org_id
        )

        if assignment_to_delete:
            deleted_value = assignment_to_delete.as_dict()
            user_role_assignment_crud_command.remove(db, id=assignment_to_delete.id)
            audit_command_provider.log(
                db=db, 
                actor_user=actor_user, 
                event_type="USER_ROLE_REVOKED",
                description=f"Role '{role.name}' revoked from user '{target_user.username}'",
                details=deleted_value
            )

user_role_assignment_command_service = UserRoleAssignmentCommandService()
