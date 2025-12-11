# services/supported_component_query_service.py

from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.supported_component_query_crud import supported_component_query_crud
from app.models.objects.supported_component import SupportedComponent

class SupportedComponentQueryService:
    """지원 부품 정보 조회 관련 서비스를 담당합니다."""

    def get_all_supported_components(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[SupportedComponent]:
        """시스템에 등록된 모든 지원 부품의 목록을 조회합니다."""
        return supported_component_query_crud.get_multi(db, skip=skip, limit=limit)

    def get_by_component_type(self, db: Session, *, component_type: str) -> Optional[SupportedComponent]:
        """컴포넌트 타입으로 지원 부품을 조회합니다."""
        return supported_component_query_crud.get_by_component_type(db, component_type=component_type)

supported_component_query_service = SupportedComponentQueryService()
