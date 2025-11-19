from sqlalchemy.orm import Session
from typing import Set

from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.organization import Organization
from app.models.relationships.user_organization_role import UserOrganizationRole # Corrected import path
from app.core.exceptions import PermissionDeniedError, DuplicateEntryError

class AuthorizationService:
    def check_user_permission(
        self, 
        db: Session, 
        *, 
        user: User, 
        permission_name: str, 
        organization_id: int | None = None
    ) -> bool:
        """
        Checks if a user has a specific permission, potentially within the scope of an organization.

        - Users with a SYSTEM-scoped role that has the permission are granted access.
        - Users with an ORGANIZATION-scoped role that has the permission are granted access
          if the organization_id matches the one provided.
        """
        # 'is_superuser' check is removed to enforce full RBAC
        for assignment in user.user_role_assignments:
            role = assignment.role
            if not role:
                continue

            # Check if the role itself has the permission
            has_perm_in_role = False
            for rp in role.permissions:
                if rp.permission and rp.permission.name == permission_name:
                    has_perm_in_role = True
                    break
            
            if not has_perm_in_role:
                continue

            # If permission is found in the role, check the scope
            if role.scope == 'SYSTEM':
                return True  # System-scoped role grants permission anywhere

            if role.scope == 'ORGANIZATION' and organization_id is not None:
                if assignment.organization_id == organization_id:
                    return True  # Org-scoped role grants permission if orgs match
        
        return False

    def assign_role_to_user(
        self,
        db: Session,
        *,
        request_user: User,
        user_to_assign: User,
        role_to_assign: Role,
        organization: Organization | None = None,
    ) -> UserOrganizationRole:
        """Assigns a role to a user, ensuring the requesting user has permission."""
        org_id = organization.id if organization else None

        # 1. Authorization Check
        if not self.check_user_permission(
            db, user=request_user, permission_name="user:assign_role", organization_id=org_id
        ):
            raise PermissionDeniedError("You do not have permission to assign roles.")

        # 2. Prevent assigning a role with a higher tier than the request_user's highest tier
        # (This logic can be added later for more granular control)

        # 3. Check for duplicate assignment
        existing_assignment = (
            db.query(UserOrganizationRole)
            .filter(
                UserOrganizationRole.user_id == user_to_assign.id,
                UserOrganizationRole.role_id == role_to_assign.id,
                UserOrganizationRole.organization_id == org_id,
            )
            .first()
        )
        if existing_assignment:
            raise DuplicateEntryError("Role assignment", "user, role, and organization")

        # 4. Create new assignment
        new_assignment = UserOrganizationRole(
            user_id=user_to_assign.id,
            role_id=role_to_assign.id,
            organization_id=org_id,
        )
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

        return new_assignment


authorization_service = AuthorizationService()
