import logging
import json
import hmac
import hashlib
from sqlalchemy.orm import Session
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class HmacIntegrityValidator:
    """
    메시지의 무결성을 검증합니다. 
    라즈베리파이 클라이언트의 json.dumps 규격과 완벽히 일치하도록 설정되었습니다.
    """
    def validate(
        self,
        db: Session,
        *,
        device: any, 
        payload: dict
    ) -> Tuple[bool, Optional[str]]:
        
        # 1. 페이로드에서 클라이언트가 보낸 서명 추출
        hmac_signature = payload.get("hmac")
        if not hmac_signature:
            return False, "HMAC signature missing"

        # 2. DB 내 장치 시크릿 키 존재 여부 확인
        if not device.hmac_secret_key:
            return False, "Device secret key missing in DB"

        # 3. 검증용 데이터 준비 (서명 필드 제외)
        payload_for_check = payload.copy()
        payload_for_check.pop("hmac", None)

        try:
            # 4. [핵심] 라즈베리파이 클라이언트와 직렬화 규격 통일
            message_str = json.dumps(
                payload_for_check, 
                sort_keys=True, 
                separators=(',', ':'),      # 공백 제거
                ensure_ascii=False,         # 유니코드 유지
                default=str                 # 날짜 객체 등 처리
            )
            
            message = message_str.encode('utf-8')
            secret = device.hmac_secret_key.encode('utf-8')

            # 5. 서버 측 서명 생성 및 비교
            expected_signature = hmac.new(
                secret, 
                message, 
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_signature, hmac_signature):
                logger.warning(f"❌ HMAC mismatch for device: {device.current_uuid}")
                return False, "HMAC integrity check failed."
            
            logger.info(f"✅ HMAC Verified: {device.current_uuid}")
            return True, None

        except Exception as e:
            logger.error(f"HMAC Error: {str(e)}")
            return False, f"HMAC error: {str(e)}"

hmac_integrity_validator = HmacIntegrityValidator()