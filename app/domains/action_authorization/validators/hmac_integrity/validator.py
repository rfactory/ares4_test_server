import logging
import json
from sqlalchemy.orm import Session
from typing import Tuple, Optional

# Providers
from app.domains.inter_domain.device_management.hmac_query_provider import hmac_query_provider

# Schemas
from app.domains.inter_domain.device_management.schemas.device_internal import DeviceWithSecret

logger = logging.getLogger(__name__)

class HmacIntegrityValidator:
    """
    이 Validator는 메시지의 '무결성'을 검증하는 단일 책임을 갖습니다.
    '무결성'이란, '메시지 내용이 위변조되지 않았음'을 의미합니다.
    HMAC 서명을 Vault Transit Engine을 통해 검증합니다.
    """
    def validate(
        self,
        db: Session,
        *,
        device: DeviceWithSecret,
        payload: dict
    ) -> Tuple[bool, Optional[str]]:
        """
        페이로드의 무결성(HMAC)을 검증합니다.
        """
        # 1. HMAC 서명 추출
        hmac_signature = payload.get("hmac")
        if not hmac_signature:
            error_msg = f"HMAC 서명이 페이로드에 없습니다. (장치 UUID: '{device.current_uuid}')."
            logger.warning(error_msg)
            return False, error_msg

        # 2. HMAC 검증 대상이 되는 페이로드 준비
        # 원본 payload를 복사하여 'hmac' 필드를 제거한 검증용 사본을 만듭니다.
        payload_for_hmac_check = payload.copy()
        payload_for_hmac_check.pop("hmac", None)

        # 3. hmac_query_provider를 통해 Vault에 검증을 위임합니다.
        is_hmac_valid = hmac_query_provider.verify_hmac(
            key_name=device.hmac_key_name,
            payload=json.dumps(payload_for_hmac_check, sort_keys=True),
            signature=hmac_signature
        )

        if not is_hmac_valid:
            error_msg = f"HMAC 검증 실패. (장치 UUID: '{device.current_uuid}'). 메시지가 위변조되었거나, 서명이 잘못되었습니다."
            logger.warning(error_msg)
            return False, error_msg
        
        # 모든 검증을 통과하면, 성공(True)을 반환합니다.
        return True, None

hmac_integrity_validator = HmacIntegrityValidator()
