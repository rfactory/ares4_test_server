import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

# inter_domain에 있는 올바른 Provider를 import 합니다.
from app.domains.inter_domain.supported_component_management.supported_component_query_provider import supported_component_query_provider

logger = logging.getLogger(__name__)

class SystemSupportValidator:
    def validate(self, db: Session, *, component_type: str) -> Tuple[bool, Optional[str]]:
        """
        컴포넌트 타입이 시스템에서 지원되는지 '판단'합니다.
        성공 시 (True, None), 실패 시 (False, "에러 메시지")를 반환합니다.
        """
        # Provider를 통해 부품이 존재하는지 조회합니다.
        supported_component = supported_component_query_provider.get_by_component_type(db, component_type=component_type)
        
        if not supported_component:
            msg = f"Component type '{component_type}' is not supported by the system."
            logger.warning(f"VALIDATOR: {msg}")
            return False, msg
        
        # 부품이 존재하므로 검증 성공
        return True, None

system_support_validator = SystemSupportValidator()