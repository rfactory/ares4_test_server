from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.action_authorization.policies.organization_management.manage_organization_member_policy import manage_organization_member_policy

class ManageOrganizationMemberPolicyProvider:
    def remove(self, db: Session, *, actor_user: User, organization_id: int, user_to_remove_id: int):
        return manage_organization_member_policy.remove(
            db, actor_user=actor_user, organization_id=organization_id, user_to_remove_id=user_to_remove_id
        )

    def update_role(self, db: Session, *, actor_user: User, organization_id: int, user_to_update_id: int, new_role_id: int):
        return manage_organization_member_policy.update_role(
            db, actor_user=actor_user, organization_id=organization_id, user_to_update_id=user_to_update_id, new_role_id=new_role_id
        )

manage_organization_member_policy_provider = ManageOrganizationMemberPolicyProvider()
