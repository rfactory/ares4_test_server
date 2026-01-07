from typing import Tuple

from app.domains.action_authorization.validators.password.password_strength_validator import validate_password_strength_policy

class PasswordStrengthValidatorProvider:
    """
    비밀번호 강도를 검증하는 validator를 외부 도메인에 노출하는 제공자입니다.
    """
    def validate_strength(self, password: str) -> Tuple[bool, str]:
        """
        제공된 비밀번호의 강도를 검증합니다.
        """
        return validate_password_strength_policy(password)

password_strength_validator_provider = PasswordStrengthValidatorProvider()
