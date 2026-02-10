from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.objects.supported_component import SupportedComponent
from ..schemas.supported_component_query import SupportedComponentQuery

class CRUDSupportedComponentQuery:
    def get_multi(self, db: Session, *, query_params: SupportedComponentQuery) -> List[SupportedComponent]:
        """
        검색 조건(query_params)에 따라 지원되는 부품 목록을 조회합니다.
        """
        query = db.query(SupportedComponent)

        # 1. model_name으로 검색 (예: SYSTEM)
        if query_params.model_name:
            query = query.filter(SupportedComponent.model_name == query_params.model_name)

        # 2. 기타 필터
        if query_params.category:
            query = query.filter(SupportedComponent.category == query_params.category)
            
        if query_params.manufacturer:
            query = query.filter(SupportedComponent.manufacturer == query_params.manufacturer)

        return query.order_by(SupportedComponent.id.asc()).offset(query_params.skip).limit(query_params.limit).all()

    # 👇 [핵심 수정] 함수 이름을 서비스가 호출하는 'get_by_component_type'으로 변경했습니다.
    def get_by_component_type(self, db: Session, *, component_type: str) -> Optional[SupportedComponent]:
        """
        텔레메트리의 'component_type'을 DB의 'model_name'과 매칭하여 조회합니다.
        (예: payload의 'SYSTEM' -> DB의 model_name='SYSTEM')
        """
        return db.query(SupportedComponent).filter(SupportedComponent.model_name == component_type).first()

supported_component_query_crud = CRUDSupportedComponentQuery()