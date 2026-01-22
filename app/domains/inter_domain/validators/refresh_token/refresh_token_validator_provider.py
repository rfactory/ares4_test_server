from typing import Optional
from app.models.objects.refresh_token import RefreshToken
from app.domains.action_authorization.validators.refresh_token.validator import refresh_token_validator

class RefreshTokenValidatorProvider:
    def validate(self, *, token_obj: Optional[RefreshToken]):
        """RefreshTokenValidator를 호출하여 토큰 객체의 유효성을 검사합니다."""
        return refresh_token_validator.validate(token_obj=token_obj)

refresh_token_validator_provider = RefreshTokenValidatorProvider()