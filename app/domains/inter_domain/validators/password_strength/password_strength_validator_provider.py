from app.domains.action_authorization.validators.password.password_strength_validator import password_strength_validator

class PasswordStrengthValidatorProvider:
    """
    비밀번호 강도를 검증하는 validator를 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(self, password: str) -> None:
        """
        제공된 비밀번호의 강도를 검증합니다. 실패 시 예외가 발생합니다.
        """
        return password_strength_validator.validate(password)

password_strength_validator_provider = PasswordStrengthValidatorProvider()
