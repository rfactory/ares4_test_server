import logging
from typing import Tuple, Optional
from app.domains.inter_domain.supported_component_management.schemas.models import SupportedComponentRead
logger = logging.getLogger(__name__)

class SystemSupportValidator:
    def validate_support(self, *, supported_component: Optional[SupportedComponentRead]) -> Tuple[bool, Optional[str]]:
        """
        시스템 지원 여부만 판단합니다. 
        데이터는 외부(Provider)에서 공급받습니다.
        """
        if not supported_component:
            return False, "The requested component type is not supported by the system."

        # 향후 특정 카테고리의 일시적 제한 등 추가 로직이 필요하면 여기에 작성합니다.
        
        logger.info(f"[Validator] System support verified for: {supported_component.component_type}")
        return True, None

system_support_validator = SystemSupportValidator()