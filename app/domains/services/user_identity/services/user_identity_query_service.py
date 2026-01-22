from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.user_identity_query_crud import user_identity_query_crud
from app.models.objects.user import User as DBUser

class UserIdentityQueryService:
    def get_user_by_id(self, db: Session, *, user_id: int) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_id(db, user_id=user_id)

    def get_user_by_username(self, db: Session, *, username: str) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_username(db, username=username)

    def get_user_by_email(self, db: Session, *, email: str) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_email(db, email=email)

    def get_user(self, db: Session, *, user_id: int) -> Optional[DBUser]:
        return user_identity_query_crud.get(db, id=user_id)

    def get_members_by_organization(self, db: Session, *, organization_id: int) -> List[dict]:
        """
        특정 조직에 속한 모든 사용자와 그들의 역할을 조회합니다.
        """
        assignments = user_identity_query_crud.get_assignments_by_context(
            db, scope='ORGANIZATION', organization_id=organization_id
        )
        
        members = []
        for assignment in assignments:
            if assignment.user and assignment.role:
                member_data = {
                    "id": assignment.user.id,
                    "username": assignment.user.username,
                    "email": assignment.user.email,
                    "role": assignment.role.name # Return only the role name
                }
                members.append(member_data)
        return members

    def get_members_by_system(self, db: Session) -> List[dict]:
        """
        시스템 역할을 가진 모든 사용자와 그들의 역할을 조회합니다.
        """
        assignments = user_identity_query_crud.get_assignments_by_context(
            db, scope='SYSTEM'
        )
        
        members = []
        for assignment in assignments:
            if assignment.user and assignment.role:
                member_data = {
                    "id": assignment.user.id,
                    "username": assignment.user.username,
                    "email": assignment.user.email,
                    "role": assignment.role.name # Return only the role name
                }
                members.append(member_data)
        return members

user_identity_query_service = UserIdentityQueryService()
