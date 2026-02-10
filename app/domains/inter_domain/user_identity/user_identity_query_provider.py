from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.user_identity.services.user_identity_query_service import user_identity_query_service, UserIdentityQueryService
from .schemas.user_identity_query import MemberResponse
from .schemas.models import User # Re-export for inter-domain usage

class UserIdentityQueryProvider:
    def get_service(self) -> UserIdentityQueryService:
        return user_identity_query_service
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return user_identity_query_service.get_user_by_id(db, user_id=user_id)

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return user_identity_query_service.get_user_by_username(db, username=username)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return user_identity_query_service.get_user_by_email(db, email=email)

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return user_identity_query_service.get_user(db, user_id=user_id)

    def get_members_by_organization(self, db: Session, *, organization_id: int) -> List[MemberResponse]:
        return user_identity_query_service.get_members_by_organization(
            db, organization_id=organization_id
        )

    def get_members_by_system(self, db: Session) -> List[MemberResponse]:
        return user_identity_query_service.get_members_by_system(db)
    
    def get_user_organization_ids(self, db: Session, *, user_id: int) -> List[int]:
        """
        사용자가 소속된 모든 조직 ID 리스트를 반환합니다. 
        (Validator의 판단 재료로 사용됨)
        """
        return user_identity_query_service.get_user_organization_ids(db, user_id=user_id)

user_identity_query_provider = UserIdentityQueryProvider()