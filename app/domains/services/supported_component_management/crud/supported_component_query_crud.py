# crud/supported_component_query_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.objects.supported_component import SupportedComponent
from ..schemas.supported_component_query import SupportedComponentRead # Query 스키마를 사용

class CRUDSupportedComponentQuery(CRUDBase[SupportedComponent, None, None]): # Command 스키마는 사용하지 않음
    def get_by_component_type(self, db: Session, *, component_type: str) -> Optional[SupportedComponent]:
        """컴포넌트 타입으로 특정 지원 부품을 조회합니다."""
        return db.query(self.model).filter(self.model.component_type == component_type).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[SupportedComponent]:
        """페이징 처리하여 여러 지원 부품을 조회합니다."""
        return db.query(self.model).offset(skip).limit(limit).all()

supported_component_query_crud = CRUDSupportedComponentQuery(SupportedComponent)
