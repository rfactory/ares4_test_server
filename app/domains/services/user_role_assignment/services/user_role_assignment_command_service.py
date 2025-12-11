# --- Command-related Service ---
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.models.objects.user import User
from app.models.objects.role import Role # Needed for headcount check
from app.models.objects.organization import Organization # 조직 존재 여부 확인용
from app.models.relationships.user_organization_role import UserOrganizationRole
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from ..crud.user_role_assignment_command_crud import user_role_assignment_crud_command
from ..schemas.user_role_assignment_command import UserRoleAssignmentCreate

class UserRoleAssignmentCommandService:
    def assign_role(
        self,
        db: Session,
        *,
        assignment_in: UserRoleAssignmentCreate,
        request_user: User,
    ) -> UserOrganizationRole:
        """
        Assigns a role to a user within an organization.
        This service assumes authorization has already been checked by a Policy.
        """
        # 방어적 확인: user_id, role_id, organization_id가 유효한지 확인
        existing_user = db.query(User).filter(User.id == assignment_in.user_id).first()
        if not existing_user:
            raise NotFoundError("User", str(assignment_in.user_id))
        
        existing_role = db.query(Role).filter(Role.id == assignment_in.role_id).first()
        if not existing_role:
            raise NotFoundError("Role", str(assignment_in.role_id))

        if assignment_in.organization_id is not None:
            existing_organization = db.query(Organization).filter(Organization.id == assignment_in.organization_id).first()
            if not existing_organization:
                raise NotFoundError("Organization", str(assignment_in.organization_id))

        # 1. Check for duplicate assignment
        existing_assignment = user_role_assignment_crud_command.get_by_user_role_org(
            db,
            user_id=assignment_in.user_id,
            role_id=assignment_in.role_id,
            organization_id=assignment_in.organization_id,
        )
        if existing_assignment:
            raise DuplicateEntryError("Role assignment", "user, role, and organization")

        # 2. Enforce Role Headcount Limits (Requires fetching the Role object)
        # Note: existing_role is already fetched above as part of defensive checks.
        if existing_role and existing_role.max_headcount is not None:
            current_count = (
                db.query(func.count(UserOrganizationRole.user_id))
                .filter(UserOrganizationRole.role_id == existing_role.id)
                .scalar()
            )
            if current_count >= existing_role.max_headcount:
                raise DuplicateEntryError(
                    f"Cannot assign {existing_role.name}. Maximum headcount of {existing_role.max_headcount} already reached."
                )

        # 3. Create new assignment via CRUD
        new_assignment = user_role_assignment_crud_command.create(db, obj_in=assignment_in)
        
        # ← 여기만 삭제하면 끝!
        # db.commit()     ← 삭제
        # db.refresh()    ← 삭제

        # 5. Audit log (Policy에서 commit 할 때 함께 저장됨)
        audit_command_provider.log_creation(
            db=db,
            actor_user=request_user,
            resource_name="UserRoleAssignment",
            resource_id=new_assignment.id,
            new_value=new_assignment.as_dict()
        )

        return new_assignment  # ← 여기서 끝! Policy에서 commit

user_role_assignment_command_service = UserRoleAssignmentCommandService()
