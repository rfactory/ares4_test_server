# --- 사용자-역할 할당 명령 Provider ---
from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.services.user_role_assignment.schemas.user_role_assignment_command import UserRoleAssignmentCreate
from app.domains.services.user_role_assignment.services.user_role_assignment_command_service import user_role_assignment_command_service

class UserRoleAssignmentCommandProvider:
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
