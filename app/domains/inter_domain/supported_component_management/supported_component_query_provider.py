from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.supported_component_management.services.supported_component_query_service import supported_component_query_service
from .schemas.models import SupportedComponentRead # Pydantic 스키마 임포트

class SupportedComponentQueryProvider:
    """
    지원 부품(Supported Component) 관련 Query 서비스의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def get_all_supported_components(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[SupportedComponentRead]:
        db_components = supported_component_query_service.get_all_supported_components(db=db, skip=skip, limit=limit)
        
        return [SupportedComponentRead.model_validate(comp) for comp in db_components]
        
    def get_by_component_type(self, db: Session, *, component_type: str) -> Optional[SupportedComponentRead]:
        db_component = supported_component_query_service.get_by_component_type(db, component_type=component_type)
        
        if not db_component:
            return None
            
        return SupportedComponentRead.model_validate(db_component)
            

supported_component_query_provider = SupportedComponentQueryProvider()
