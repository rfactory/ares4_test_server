# inter_domain/validators/system_support/provider.py

from sqlalchemy.orm import Session
from typing import Tuple, Optional

# Validator 임포트
from app.domains.action_authorization.validators.system_support.validator import system_support_validator

class SystemSupportValidatorProvider:
    """
    SystemSupportValidator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(
        self,
        db: Session,
        *,
        component_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        컴포넌트 타입이 시스템에서 지원되는지 '판단'을 위임합니다.
        """
        return system_support_validator.validate(
            db=db,
            component_type=component_type
        )

system_support_validator_provider = SystemSupportValidatorProvider()
