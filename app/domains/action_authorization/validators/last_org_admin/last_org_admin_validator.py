from sqlalchemy.orm import Session
from typing import List

from app.core.exceptions import ForbiddenError
from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.relationships.user_organization_role import UserOrganizationRole

class LastOrgAdminValidator:
    def validate(self, db: Session, *, target_user: User, roles_to_revoke: List[Role]):
        """
        조직의 마지막 tier=1 관리자 또는 시스템의 마지막 System_Admin이 역할을 해제하는 것을 방지합니다.
        """
        for role in roles_to_revoke:
            is_assigned = any(
                assignment.role_id == role.id and assignment.user_id == target_user.id
                for assignment in target_user.user_role_assignments
            )
            if not is_assigned:
                continue

            # 규칙 1: 조직의 마지막 tier=1 관리자 이탈 방지
            if role.tier == 1 and role.organization_id is not None:
                other_admins_count = (
                    db.query(UserOrganizationRole)
                    .filter(
                        UserOrganizationRole.organization_id == role.organization_id,
                        UserOrganizationRole.role.has(tier=1),
                        UserOrganizationRole.user_id != target_user.id
                    )
                    .count()
                )
                if other_admins_count == 0:
                    raise ForbiddenError(
                        f"You are the last administrator (tier 1) of the organization. "
                        f"Please appoint another administrator before revoking your own role."
                    )
            
            # 규칙 2: 시스템의 마지막 System_Admin 이탈 방지
            if role.name == "System_Admin":
                other_system_admins_count = (
                    db.query(UserOrganizationRole)
                    .filter(
                        UserOrganizationRole.role_id == role.id, # role.id가 System_Admin 역할의 ID임
                        UserOrganizationRole.user_id != target_user.id
                    )
                    .count()
                )
                if other_system_admins_count == 0:
                    raise ForbiddenError(
                        "You are the last System_Admin. You cannot revoke your own role."
                    )

last_org_admin_validator = LastOrgAdminValidator()
