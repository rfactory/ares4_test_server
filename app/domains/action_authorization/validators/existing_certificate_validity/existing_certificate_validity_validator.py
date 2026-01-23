import logging
from typing import Tuple, Optional, Dict
from datetime import datetime, timezone, timedelta
from app.core.config import Settings
from app.domains.services.certificate_management.schemas import IssuedCertificateRead

logger = logging.getLogger(__name__)

class ExistingCertificateValidityValidator:
    """
    기존 인증서의 유효성을 검사하는 Validator입니다.
    - 인증서의 만료 기간이 충분히 남아있는지 확인합니다.
    - 만료 임박 기준 시간(예: 1시간)은 설정에서 가져올 수 있습니다.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def validate(self, certificate_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        인증서 데이터의 만료 시각을 확인하여 유효성을 검증합니다.

        Args:
            certificate_data: IssuedCertificateRead 스키마에 해당하는 딕셔너리.
                            'expiration' 키에 datetime 객체가 포함되어야 합니다.

        Returns:
            (True, None) - 인증서가 충분히 유효할 경우
            (False, 에러 메시지) - 인증서가 만료되었거나 만료 임박했을 경우
        """
        if not certificate_data or not isinstance(certificate_data, Dict):
            return False, "Invalid certificate data provided."
        
        try:
            # IssuedCertificateRead 스키마를 사용하여 데이터 유효성 검사
            cert_info = IssuedCertificateRead(**certificate_data)
        except Exception as e:
            return False, f"Certificate data does not match schema: {e}"

        if not cert_info.expiration:
            return False, "Certificate expiration date is missing."

        now = datetime.now(timezone.utc)
        
        # 만료되었는지 확인
        if cert_info.expiration <= now:
            return False, "Certificate has expired."
        
        # 동적 임계값 판단(전체 수명의 10% 또는 최소 12시간)
        # Threshold = max(43200, total_ttl * 0.1)
        total_ttl = (cert_info.expiration - cert_info.issued_at).total_seconds()
        remaining = (cert_info.expiration - now).total_seconds()
        
        dynamic_threshold = max(12 * 3600, total_ttl * 0.1)
        
        if remaining < dynamic_threshold:
            return False, f"Certificate is expiring soon (within {dynamic_threshold / 3600} hours)."
        
        return True, None
        
# --- Singleton Instance ---
app_settings = Settings()
existing_certificate_validity_validator = ExistingCertificateValidityValidator(settings=app_settings)