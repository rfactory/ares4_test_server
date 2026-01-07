from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.objects.user import User as DBUser

# Schemas from other domains are the 'contract' for the coordinator to use
from app.domains.inter_domain.user_identity.schemas.user_identity_command import UserCreate
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestCreate, AccessRequestUpdate
from app.domains.inter_domain.access_requests.schemas.access_request_query import AccessRequestRead

# Inter-domain providers
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.access_requests.access_requests_command_provider import access_request_command_providers
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider

class UserManagementCoordinator:
    async def create_user_and_request_access(
        self,
        db: Session,
        *,
        access_request_in: AccessRequestCreate,
    ) -> AccessRequestRead:
        """
        Orchestrates the creation of a user (if they don't exist) and an access request for that user.
        This is a high-level workflow for initiating user and access request.
        """
        target_user = user_identity_query_provider.get_user_by_email(db, email=access_request_in.email)
        if not target_user:
            if not access_request_in.password or not access_request_in.username:
                raise ValueError("Password and username are required for new user registrations.")
            user_in_create = UserCreate(
                username=access_request_in.username,
                email=access_request_in.email,
                password=access_request_in.password
            )
            target_user = await user_identity_query_provider.create_user_and_log(db, user_in=user_in_create, is_active=False)

        db_access_request = await access_request_command_providers.create_access_request(
            db=db,
            request_in=access_request_in,
            user_id=target_user.id,
            actor_user=target_user
        )
        return db_access_request

    def get_access_requests(self, db: Session, *, current_user: DBUser, skip: int = 0, limit: int = 100, status: Optional[str] = "pending") -> List[AccessRequestRead]:
        """
        Orchestrates retrieving access requests.
        """
        return access_request_query_provider.get_pending_requests_for_actor(db, actor_user=current_user, organization_id=None)

    async def process_access_request_workflow(
        self,
        db: Session,
        *,
        request_id: int,
        update_in: AccessRequestUpdate,
        admin_user: DBUser
    ) -> AccessRequestRead:
        """
        Orchestrates the processing (approval/rejection) of an access request.
        """
        if update_in.status == "approved":
            from app.domains.inter_domain.policies.access_requests.approve_request_policy_provider import approve_request_policy_provider
            return approve_request_policy_provider.execute(db=db, request_id=request_id, admin_user=admin_user)
        elif update_in.status == "rejected":
            from app.domains.inter_domain.policies.access_requests.reject_request_policy_provider import reject_request_policy_provider
            return reject_request_policy_provider.execute(db=db, request_id=request_id, admin_user=admin_user)

user_management_coordinator = UserManagementCoordinator()