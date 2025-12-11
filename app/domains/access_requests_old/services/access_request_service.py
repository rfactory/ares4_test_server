from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.objects.user import User as DBUser
from app.models.objects.access_request import AccessRequest
from app.domains.organizations.crud.organization_crud import organization_crud
from app.domains.audit.services.audit_service import audit_service
from app.domains.inter_domain.user_management.providers import user_management_providers
from app.core.exceptions import PermissionDeniedError, NotFoundError, AlreadyExistsError
from app.core.authorization import authorization_service
from ..crud.access_request_crud import access_request_crud
from ..schemas.access_request import AccessRequestCreate, AccessRequestUpdate
from app.domains.user_management.schemas.user import UserCreate # For creating user via inter-domain provider
from app.domains.user_management.crud.account_crud import role_crud # Need role_crud for process_access_request


class AccessRequestService:
    async def create_access_request(self, db: Session, *, request_in: AccessRequestCreate, request_user: Optional[DBUser] = None) -> AccessRequest:
        organization_id: Optional[int] = None
        if request_in.business_registration_number:
            organization = organization_crud.get_by_registration_number(db, registration_number=request_in.business_registration_number)
            if not organization:
                raise NotFoundError(resource_name="Organization", resource_id=request_in.business_registration_number)
            organization_id = organization.id

        target_user = user_management_providers.get_user_by_email(db, email=request_in.email)
        
        if not target_user:
            if not request_in.password or not request_in.username:
                raise ValueError("Password and username are required for new user access requests.")
            user_in_create = UserCreate(username=request_in.username, email=request_in.email, password=request_in.password)
            target_user = await user_management_providers.create_user_and_log(db, user_in=user_in_create, is_active=False)

        if request_user and request_user.id != target_user.id:
            pass # This logic needs refinement based on who can request for whom

        existing_pending_request = access_request_crud.get_multi(db, user_id=target_user.id, requested_role_id=request_in.requested_role_id, status="pending")
        if existing_pending_request:
            raise AlreadyExistsError("An active access request for this role already exists for the user.")

        db_access_request = access_request_crud.create(db, request_in=request_in, user_id=target_user.id, organization_id=organization_id)
        
        actor = request_user if request_user else target_user
        audit_service.log(db=db, event_type="ACCESS_REQUEST_CREATED", description=f"Access request created for user '{target_user.username}' for role ID {request_in.requested_role_id}.", actor_user=actor, target_user=target_user, details={"request_id": db_access_request.id, "requested_role_id": request_in.requested_role_id})
        
        return db_access_request

    def get_access_requests(self, db: Session, *, current_user: DBUser, skip: int = 0, limit: int = 100, status: Optional[str] = "pending") -> List[AccessRequest]:
        """Lists access requests, for admins only."""
        if not authorization_service.check_user_permission(db, user=current_user, permission_name="access_request:read"):
            raise PermissionDeniedError("You do not have permission to view access requests.")
        # In a multi-tenant system, this would be further filtered by the admin's organization(s)
        return access_request_crud.get_multi(db, skip=skip, limit=limit, status=status)

    async def process_access_request(self, db: Session, *, request_id: int, update_in: AccessRequestUpdate, admin_user: DBUser) -> AccessRequest:
        """
        Approves or rejects an access request.
        """
        request_obj = access_request_crud.get(db, request_id=request_id)
        if not request_obj or request_obj.status != 'pending':
            raise NotFoundError("Pending access request not found.")

        target_user = None
        if update_in.status == 'approved':
            if not authorization_service.check_user_permission(db, user=admin_user, permission_name="access_request:approve"):
                raise PermissionDeniedError("You do not have permission to approve requests.")
            
            target_user = user_management_providers.get_user(db, id=request_obj.user_id) # Get user via provider
            if not target_user:
                raise NotFoundError("Target user for upgrade not found.")
            
            # Activate user if they were inactive (for new registrations)
            if not target_user.is_active:
                user_management_providers.activate_user(db, user_id=target_user.id) # Activate user via provider

            role_to_assign = role_crud.get(db, id=request_obj.requested_role_id)
            if not role_to_assign:
                raise NotFoundError("Requested role not found.")
            
            # Assign role via user_management_providers
            user_management_providers.assign_role_to_user(db, request_user=admin_user, user_to_assign=target_user, role_to_assign=role_to_assign)
            
            event_type = "ACCESS_REQUEST_APPROVED"
            description = f"Access request {request_id} for '{target_user.email}' was approved by {admin_user.username}."
        
        elif update_in.status == 'rejected':
            if not authorization_service.check_user_permission(db, user=admin_user, permission_name="access_request:reject"):
                raise PermissionDeniedError("You do not have permission to reject requests.")
            target_user = user_management_providers.get_user(db, id=request_obj.user_id)
            event_type = "ACCESS_REQUEST_REJECTED"
            description = f"Access request {request_id} for '{target_user.email}' was rejected by {admin_user.username}."
        else:
            raise ValueError("Invalid status provided for access request.")
        
        updated_request = access_request_crud.update_status(db, db_obj=request_obj, update_in=update_in, admin_user_id=admin_user.id)
        
        audit_service.log(
            db=db,
            event_type=event_type,
            description=description,
            actor_user=admin_user,
            target_user=target_user,
            details={"request_id": request_id, "rejection_reason": update_in.rejection_reason}
        )
        return updated_request

access_request_service = AccessRequestService()
