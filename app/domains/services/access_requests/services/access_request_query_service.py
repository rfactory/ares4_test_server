from sqlalchemy.orm import Session
from typing import List, Optional

# 필요한 모델 import 추가
from app.models.objects.user import User # 현재 사용되지 않지만, 다른 메소드에 필요할 수 있음
from app.models.objects.access_request import AccessRequest # CRUD에서 반환하는 모델 타입 명시를 위해 추가

from ..crud.access_request_query_crud import access_request_crud_query
from ..schemas.access_request_query import AccessRequestQuery, AccessRequestRead

class AccessRequestQueryService:
    def get_access_requests(self, db: Session, *, query_params: AccessRequestQuery, current_user: User) -> List[AccessRequestRead]:
        """접근 요청 목록을 조회합니다."""
        access_requests = access_request_crud_query.get_multi(db, query_params=query_params)

        return [AccessRequestRead.from_orm(req) for req in access_requests]

    def get_access_request_by_id(self, db: Session, *, request_id: int, current_user: User) -> Optional[AccessRequestRead]:
        """ID로 단일 접근 요청을 조회합니다."""
        access_request = access_request_crud_query.get(db, id=request_id)
        if not access_request:
            return None

        return AccessRequestRead.from_orm(access_request)

    def get_pending_access_request_by_user_org( # 함수 이름 변경 및 role_id 인자 제거
        self,
        db: Session,
        *,
        user_id: int,
        organization_id: Optional[int]
    ) -> Optional[AccessRequest]:
        """
        한 사용자가 특정 조직에 대해 보류 중인(pending) 접근 요청을 이미 가지고 있는지 확인합니다.
        """
        return access_request_crud_query.get_pending_request_by_user_org(
            db,
            user_id=user_id,
            organization_id=organization_id
        )

access_request_query_service = AccessRequestQueryService()
