from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.user_identity_query_crud import user_identity_query_crud
from app.models.objects.user import User as DBUser
from ..schemas.user_identity_query import MemberResponse

class UserIdentityQueryService:
    def get_user_by_id(self, db: Session, *, user_id: int) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_id(db, user_id=user_id)

    def get_user_by_username(self, db: Session, *, username: str) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_username(db, username=username)

    def get_user_by_email(self, db: Session, *, email: str) -> Optional[DBUser]:
        return user_identity_query_crud.get_by_email(db, email=email)

    def get_user(self, db: Session, *, user_id: int) -> Optional[DBUser]:
        return user_identity_query_crud.get(db, id=user_id)

    def get_members_by_organization(self, db: Session, *, organization_id: int) -> List[MemberResponse]:
        """
        특정 조직에 속한 모든 사용자와 그들의 역할을 조회합니다.
        """
        assignments = user_identity_query_crud.get_assignments_by_context(
            db, scope='ORGANIZATION', organization_id=organization_id
        )
        
        members = []
        for assignment in assignments:
            # assignment.user가 None이 아닌지 확인하고 데이터를 추출합니다.
            if assignment.user and assignment.role:
                # 딕셔너리 대신 MemberResponse 객체로 생성하여 타입 문제를 원천 차단합니다.
                member = MemberResponse(
                    id=assignment.user.id,
                    username=assignment.user.username,
                    email=assignment.user.email,
                    role=assignment.role.name
                )
                members.append(member)
        return members

    def get_members_by_system(self, db: Session) -> List[MemberResponse]:
        """시스템 멤버 조회 로직도 동일하게 MemberResponse를 사용합니다."""
        assignments = user_identity_query_crud.get_assignments_by_context(db, scope='SYSTEM')
        
        members = []
        for assignment in assignments:
            if assignment.user and assignment.role:
                members.append(MemberResponse(
                    id=assignment.user.id,
                    username=assignment.user.username,
                    email=assignment.user.email,
                    role=assignment.role.name
                ))
        return members
    
    def get_user_organization_ids(self, db: Session, *, user_id: int) -> List[int]:
        """
        사용자가 멤버로 속해 있는 모든 조직의 ID 리스트를 조회합니다.
        """
        # 기존에 존재하는 get_assignments_by_context를 활용 (scope을 지정하지 않거나 USER 기준으로 필터)
        # 만약 crud에 get_assignments_by_user가 있다면 그것을 사용하고, 
        # 없다면 아래와 같이 로직을 구성합니다.
        assignments = user_identity_query_crud.get_assignments_by_context(
            db, scope='ORGANIZATION' # 조직 단위 할당 정보를 모두 가져옴
        )
        
        # 전체 할당 중 해당 유저의 것만 필터링하여 조직 ID 추출
        return [
            a.organization_id for a in assignments 
            if a.user_id == user_id and a.organization_id is not None
        ]

user_identity_query_service = UserIdentityQueryService()
