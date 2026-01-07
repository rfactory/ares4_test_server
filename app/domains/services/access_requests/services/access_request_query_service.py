from sqlalchemy.orm import Session
from typing import List, Optional

# 필요한 모델 import 추가
from app.models.objects.user import User
from app.models.objects.access_request import AccessRequest

from ..crud.access_request_query_crud import access_request_crud_query
from ..schemas.access_request_query import AccessRequestQuery, AccessRequestRead

class AccessRequestQueryService:
    def get_pending_requests_for_actor(
        self, db: Session, *, actor_user: User, organization_id: Optional[int]
    ) -> List[AccessRequestRead]:
        """현재 actor가 볼 수 있는 보류중인 요청 목록을 반환합니다."""
        query_params = AccessRequestQuery(status="pending")

        # actor가 System_Admin인지 확인
        is_system_admin = any(r.role.name == "System_Admin" for r in actor_user.user_role_assignments)

        if is_system_admin:
            # 시스템 관리자는 모든 보류중인 요청을 볼 수 있음
            pass # organization_id 필터 없이 진행
        elif organization_id:
            # 조직 관리자는 해당 조직의 요청만 볼 수 있음
            query_params.organization_id = organization_id
        else:
            # 그 외의 경우 (예: 개인 컨텍스트의 일반 사용자)는 볼 수 있는 요청이 없음
            return []
        
        access_requests = access_request_crud_query.get_multi(db, query_params=query_params)
        return [AccessRequestRead.from_orm(req) for req in access_requests]

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

    def get_pending_by_user_role_org(
        self,
        db: Session,
        *,
        user_id: int,
        requested_role_id: int,
        organization_id: Optional[int]
    ) -> Optional[AccessRequest]:
        """
        특정 사용자, 역할, 조직에 대한 보류 중인 접근 요청을 조회합니다.
        """
        return access_request_crud_query.get_pending_by_user_role_org(
            db,
            user_id=user_id,
            requested_role_id=requested_role_id,
            organization_id=organization_id
        )

    def get_by_verification_code(self, db: Session, *, code: str) -> Optional[AccessRequest]:
        """인증 코드로 접근 요청을 조회합니다."""
        return access_request_crud_query.get_by_verification_code(db, code=code)

access_request_query_service = AccessRequestQueryService()
