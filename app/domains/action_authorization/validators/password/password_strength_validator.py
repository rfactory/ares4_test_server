from app.core.exceptions import ValidationError

class PasswordStrengthValidator:
    def validate(self, password: str):
        """
        제공된 비밀번호의 강도를 사전 정의된 기준에 따라 검증합니다.
        실패 시 ValidationError 예외를 발생시킵니다.
        """
        min_length = 8
        has_uppercase = any(char.isupper() for char in password)
        has_lowercase = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special = any(not char.isalnum() for char in password)

        if len(password) < min_length:
            raise ValidationError(f"Password must be at least {min_length} characters long.")
        if not has_uppercase:
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not has_lowercase:
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not has_digit:
            raise ValidationError("Password must contain at least one digit.")
        if not has_special:
            raise ValidationError("Password must contain at least one special character.")

password_strength_validator = PasswordStrengthValidator()
