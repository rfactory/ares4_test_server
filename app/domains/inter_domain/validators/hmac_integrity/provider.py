# inter_domain/validators/hmac_integrity/provider.py

from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict

# Validator 임포트
from app.domains.action_authorization.validators.hmac_integrity.validator import hmac_integrity_validator
# 스키마 임포트 (Validator에게 넘겨줄 device 객체의 타입 힌팅용)
from app.domains.inter_domain.device_management.schemas.device_internal import DeviceWithSecret

class HmacIntegrityValidatorProvider:
    """
    HmacIntegrityValidator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(
        self,
        db: Session,
        *,
        device: DeviceWithSecret,
        payload: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        페이로드의 무결성(HMAC)을 검증하는 '판단'을 위임합니다.
        """
        return hmac_integrity_validator.validate(
            db=db,
            device=device,
            payload=payload
        )

hmac_integrity_validator_provider = HmacIntegrityValidatorProvider()
