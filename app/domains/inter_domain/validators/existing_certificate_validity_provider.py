from typing import Tuple, Optional, Dict

from app.domains.action_authorization.validators.existing_certificate_validity.existing_certificate_validity_validator import existing_certificate_validity_validator

class ExistingCertificateValidityValidatorProvider:
    """
    `existing_certificate_validity` validator의 기능을 외부 도메인에 노출하는 제공자입니다.
    `Validator`를 직접 호출합니다.
    """
    def validate(self, certificate_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        인증서 데이터의 유효성을 검증합니다。
        """
        return existing_certificate_validity_validator.validate(certificate_data)

existing_certificate_validity_provider = ExistingCertificateValidityValidatorProvider()
