from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.access_requests.services.access_request_query_service import access_request_query_service
# inter_domain 내의 스키마 재수출 파일을 사용하도록 수정
from .schemas.access_request_query import AccessRequestQuery, AccessRequestRead
from app.models.objects.user import User # User 모델 import 추가

class AccessRequestQueryProviders:
    def get_access_requests(self, db: Session, *, query_params: AccessRequestQuery) -> List[AccessRequestRead]:
        """접근 요청 목록을 조회하는 안정적인 인터페이스를 제공합니다."""
        return access_request_query_service.get_access_requests(db, query_params=query_params)
    
    def get_access_request_by_id(self, db: Session, *, request_id: int) -> Optional[AccessRequestRead]:
        """ID로 단일 접근 요청을 조회하는 안정적인 인터페이스를 제공합니다."""
        return access_request_query_service.get_access_request_by_id(db, request_id=request_id)
    
    def get_pending_requests_for_actor(
        self, db: Session, *, actor_user: User, organization_id: Optional[int]
    ) -> List[AccessRequestRead]:
        """현재 actor가 볼 수 있는 보류중인 요청 목록을 조회합니다."""
        return access_request_query_service.get_pending_requests_for_actor(db, actor_user=actor_user, organization_id=organization_id)

    def get_pending_access_request_by_user_org(
        self,
        db: Session,
        *,
        user_id: int,
        organization_id: Optional[int]
    ) -> Optional[AccessRequestRead]:
        """
        한 사용자가 특정 조직에 대해 보류 중인(pending) 접근 요청을 이미 가지고 있는지 확인합니다.
        """
        access_request_model = access_request_query_service.get_pending_access_request_by_user_org(
            db,
            user_id=user_id,
            organization_id=organization_id
        )
        if not access_request_model: # 로직 오류 수정: 모델이 없을 때 None 반환
            return None
        
        # Pydantic v2에 맞게 model_validate 사용
        return AccessRequestRead.model_validate(access_request_model)

    def get_pending_by_user_role_org(
        self,
        db: Session,
        *,
        user_id: int,
        requested_role_id: int,
        organization_id: Optional[int]
    ) -> Optional[AccessRequestRead]:
        """
        특정 사용자, 역할, 조직에 대한 보류 중인 접근 요청을 조회합니다.
        """
        access_request_model = access_request_query_service.get_pending_by_user_role_org(
            db,
            user_id=user_id,
            requested_role_id=requested_role_id,
            organization_id=organization_id
        )
        if not access_request_model:
            return None

        return AccessRequestRead.model_validate(access_request_model)

    def get_by_verification_code(self, db: Session, *, code: str) -> Optional[AccessRequestRead]:
        """인증 코드로 접근 요청을 조회합니다."""
        access_request_model = access_request_query_service.get_by_verification_code(db, code=code)
        if not access_request_model:
            return None
        return AccessRequestRead.model_validate(access_request_model)

access_request_query_provider = AccessRequestQueryProviders()