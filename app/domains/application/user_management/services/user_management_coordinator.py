from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.objects.user import User as DBUser

# Schemas from other domains are the 'contract' for the coordinator to use
from app.domains.services.user_identity.schemas.user import UserCreate
from app.domains.services.access_requests.schemas.access_request import AccessRequestCreate, AccessRequestUpdate, AccessRequestResponse

# Inter-domain providers
from app.domains.inter_domain.user_identity.providers import user_identity_providers
from server2.app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_providers

class UserManagementCoordinator:
    async def create_user_and_request_access(
        self,
        db: Session,
        *,
        access_request_in: AccessRequestCreate,
    ) -> AccessRequestResponse:
        """
        Orchestrates the creation of a user (if they don't exist) and an access request for that user.
        This is a high-level workflow for initiating user and access request.
        """
        # 1. User Creation/Retrieval (delegated to user_identity service)
        target_user = user_identity_providers.get_user_by_email(db, email=access_request_in.email)
        if not target_user:
            if not access_request_in.password or not access_request_in.username:
                raise ValueError("Password and username are required for new user registrations.")
            user_in_create = UserCreate(
                username=access_request_in.username,
                email=access_request_in.email,
                password=access_request_in.password
            )
            target_user = await user_identity_providers.create_user_and_log(db, user_in=user_in_create, is_active=False)

        # 2. Access Request Creation (delegated to access_requests service)
        # Note: The `request_user` is None here, as this workflow is initiated by an unauthenticated user.
        # The service will handle the actor logging appropriately.
        db_access_request = await access_request_providers.create_access_request(
            db=db,
            request_in=access_request_in,
            request_user=None
        )
        return db_access_request

    def get_access_requests(self, db: Session, *, current_user: DBUser, skip: int = 0, limit: int = 100, status: Optional[str] = "pending") -> List[AccessRequestResponse]:
        """
        Orchestrates retrieving access requests.
        """
        # This is a simple pass-through for now, but could contain more complex logic later.
        return access_request_providers.get_access_requests(db, current_user=current_user, skip=skip, limit=limit, status=status)

    async def process_access_request_workflow(
        self,
        db: Session,
        *,
        request_id: int,
        update_in: AccessRequestUpdate,
        admin_user: DBUser
    ) -> AccessRequestResponse:
        """
        Orchestrates the processing (approval/rejection) of an access request.
        """
        return await access_request_providers.process_access_request(
            db=db,
            request_id=request_id,
            update_in=update_in,
            admin_user=admin_user
        )

user_management_coordinator = UserManagementCoordinator()