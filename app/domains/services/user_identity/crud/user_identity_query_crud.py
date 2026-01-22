from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.objects.user import User
from app.models.relationships.user_organization_role import UserOrganizationRole
from ..schemas.user_identity_command import UserCreate, UserUpdate # Even query CRUD needs these for the base class

class CRUDUserQuery(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_id(self, db: Session, *, user_id: int) -> Optional[User]:
        return super().get(db, id=user_id)

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_assignments_by_context(self, db: Session, *, scope: str, organization_id: Optional[int] = None) -> List[UserOrganizationRole]:
        """
        주어진 컨텍스트에 대한 모든 역할 할당 정보를 조회합니다.
        scope가 'SYSTEM'이면 시스템 역할을, 'ORGANIZATION'이면 해당 조직의 역할을 조회합니다.
        """
        query = (
            db.query(UserOrganizationRole)
            .options(
                joinedload(UserOrganizationRole.user),
                joinedload(UserOrganizationRole.role)
            )
        )

        if scope == 'SYSTEM':
            query = query.filter(UserOrganizationRole.organization_id.is_(None))
        elif scope == 'ORGANIZATION' and organization_id is not None:
            query = query.filter(UserOrganizationRole.organization_id == organization_id)
        else:
            return [] # 유효하지 않은 scope 또는 organization_id가 없는 경우 빈 리스트 반환

        return query.all()

user_identity_query_crud = CRUDUserQuery(model=User)
