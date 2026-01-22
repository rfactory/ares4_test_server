from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.action_authorization.policies.system_management.manage_system_member_policy import manage_system_member_policy

class ManageSystemMemberPolicyProvider:
    def remove(self, db: Session, *, actor_user: User, user_to_remove_id: int):
        return manage_system_member_policy.remove(db=db, actor_user=actor_user, user_to_remove_id=user_to_remove_id)

    async def update_role(self, db: Session, *, actor_user: User, target_user_id: int, new_role_id: int):
        return await manage_system_member_policy.update_role(
            db=db, 
            actor_user=actor_user, 
            target_user_id=target_user_id, 
            new_role_id=new_role_id
        )

manage_system_member_policy_provider = ManageSystemMemberPolicyProvider()