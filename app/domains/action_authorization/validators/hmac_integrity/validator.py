import logging
import json
import hmac
import hashlib
from sqlalchemy.orm import Session
from typing import Tuple, Optional

# Schemas - 우리가 방금 hmac_secret_key를 추가한 그 스키마입니다.
from app.domains.inter_domain.device_management.schemas.device_internal import DeviceWithSecret

logger = logging.getLogger(__name__)

class HmacIntegrityValidator:
    """
    이 Validator는 메시지의 '무결성'을 검증합니다.
    [실전 모드] Vault를 거치지 않고, DB의 장치별 고유 시크릿 키로 직접 HMAC-SHA256을 계산합니다.
    """
    def validate(
        self,
        db: Session,
        *,
        device: DeviceWithSecret,
        payload: dict
    ) -> Tuple[bool, Optional[str]]:
        
        # 1. 페이로드에서 클라이언트가 보낸 서명 추출
        hmac_signature = payload.get("hmac")
        if not hmac_signature:
            error_msg = f"HMAC 서명이 페이로드에 없습니다. (장치: '{device.current_uuid}')"
            logger.warning(error_msg)
            return False, error_msg

        # 2. DB 시크릿 키 존재 확인
        if not device.hmac_secret_key:
            error_msg = f"DB에 장치 시크릿 키가 없습니다. (장치: '{device.current_uuid}')"
            logger.error(error_msg)
            return False, error_msg

        # 3. 검증용 데이터 준비 (hmac 필드 제거)
        payload_for_check = payload.copy()
        payload_for_check.pop("hmac", None)

        # 4. [중요] 직렬화 및 바이너리 변환
        # 라즈베리파이의 json.dumps(sort_keys=True)와 완벽히 일치해야 합니다.
        message = json.dumps(payload_for_check, sort_keys=True).encode('utf-8')
        secret = device.hmac_secret_key.encode('utf-8')

        # 5. 서버에서 직접 HMAC 서명 생성
        expected_signature = hmac.new(
            secret, 
            message, 
            hashlib.sha256
        ).hexdigest()

        # 6. [보안] 서명 비교 (타이밍 공격 방지를 위해 compare_digest 사용)
        if not hmac.compare_digest(expected_signature, hmac_signature):
            error_msg = f"HMAC 검증 실패. 메시지가 위변조되었거나 키가 다릅니다. (장치: '{device.current_uuid}')"
            logger.warning(error_msg)
            # 디버깅을 위해 서버 로그에는 계산된 서명과 받은 서명을 살짝 남길 수 있습니다 (운영 시 삭제 권장)
            # logger.debug(f"Expected: {expected_signature} / Received: {hmac_signature}")
            return False, error_msg
        
        logger.info(f"✅ HMAC Integrity Verified: {device.current_uuid}")
        return True, None

hmac_integrity_validator = HmacIntegrityValidator()