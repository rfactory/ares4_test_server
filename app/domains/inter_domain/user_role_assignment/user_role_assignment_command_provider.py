# --- 사용자-역할 할당 명령 Provider ---
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.services.user_role_assignment.schemas.user_role_assignment_command import UserRoleAssignmentCreate
from app.domains.services.user_role_assignment.services.user_role_assignment_command_service import user_role_assignment_command_service

class UserRoleAssignmentCommandProvider:
    def update_user_roles(
        self,
        db: Session,
        *,
        target_user: User,
        roles_to_assign: Optional[List[Role]] = None,
        roles_to_revoke: Optional[List[Role]] = None,
        actor_user: User,
    ) -> None:
        """사용자 역할을 일괄 업데이트하는 서비스 로직을 호출합니다."""
        return user_role_assignment_command_service.update_user_roles(
            db=db,
            target_user=target_user,
            roles_to_assign=roles_to_assign,
            roles_to_revoke=roles_to_revoke,
            actor_user=actor_user
        )

    def assign_role(
        self,
        db: Session,
        *,
        assignment_in: UserRoleAssignmentCreate,
        request_user: User,
    ) -> UserOrganizationRole:
        """
        사용자에게 역할을 할당하는 안정적인 인터페이스를 제공합니다.
        Policy 계층에서 호출될 것을 예상합니다.
        """
        return user_role_assignment_command_service.assign_role(
            db=db,
            assignment_in=assignment_in,
            request_user=request_user
        )

user_role_assignment_command_provider = UserRoleAssignmentCommandProvider()
