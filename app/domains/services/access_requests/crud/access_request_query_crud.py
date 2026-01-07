from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.objects.access_request import AccessRequest
from ..schemas.access_request_query import AccessRequestQuery

class CRUDAccessRequestQuery:
    def get(self, db: Session, *, id: int) -> Optional[AccessRequest]:
        """ID로 접근 요청을 조회합니다."""
        return db.query(AccessRequest).options(
            joinedload(AccessRequest.user),
            joinedload(AccessRequest.organization),
            joinedload(AccessRequest.requested_role)
        ).filter(AccessRequest.id == id).first()

    def get_pending_request_by_user_org( # 함수 이름 변경 및 role_id 인자 제거
        self,
        db: Session,
        *,
        user_id: int,
        organization_id: Optional[int]
    ) -> Optional[AccessRequest]:
        """
        한 사용자가 특정 조직에 대해 보류 중인(pending) 접근 요청을 이미 가지고 있는지 확인합니다.
        """
        query = db.query(AccessRequest).options(
            joinedload(AccessRequest.user),
            joinedload(AccessRequest.organization),
            joinedload(AccessRequest.requested_role)
        ).filter(
            AccessRequest.user_id == user_id,
            AccessRequest.status == "pending"
            # AccessRequest.requested_role_id 필터 제거
        )
        
        if organization_id is not None:
            query = query.filter(AccessRequest.organization_id == organization_id)
        else:
            query = query.filter(AccessRequest.organization_id.is_(None))
        
        return query.first()

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
        query = db.query(AccessRequest).options(
            joinedload(AccessRequest.user),
            joinedload(AccessRequest.organization),
            joinedload(AccessRequest.requested_role)
        ).filter(
            AccessRequest.user_id == user_id,
            AccessRequest.requested_role_id == requested_role_id,
            AccessRequest.status == "pending"
        )

        if organization_id is not None:
            query = query.filter(AccessRequest.organization_id == organization_id)
        else:
            query = query.filter(AccessRequest.organization_id.is_(None))

        return query.first()

    def get_by_verification_code(self, db: Session, *, code: str) -> Optional[AccessRequest]:
        """인증 코드로 접근 요청을 조회합니다."""
        return db.query(AccessRequest).options(
            joinedload(AccessRequest.user),
            joinedload(AccessRequest.organization),
            joinedload(AccessRequest.requested_role)
        ).filter(AccessRequest.verification_code == code).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        query_params: AccessRequestQuery
    ) -> List[AccessRequest]:
        """AccessRequestQuery 스키마를 기반으로 동적으로 쿼리하여 접근 요청 목록을 조회합니다."""
        query = db.query(AccessRequest).options(
            joinedload(AccessRequest.user),
            joinedload(AccessRequest.organization),
            joinedload(AccessRequest.requested_role)
        )

        if query_params.status:
            query = query.filter(AccessRequest.status == query_params.status)
        if query_params.user_id:
            query = query.filter(AccessRequest.user_id == query_params.user_id)
        if query_params.requested_role_id:
            query = query.filter(AccessRequest.requested_role_id == query_params.requested_role_id)
        if query_params.organization_id:
            query = query.filter(AccessRequest.organization_id == query_params.organization_id)

        return query.order_by(AccessRequest.created_at.desc()).offset(query_params.skip).limit(query_params.limit).all()

access_request_crud_query = CRUDAccessRequestQuery()