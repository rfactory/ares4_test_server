from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import AuthenticationError
from app.models.objects.refresh_token import RefreshToken

class RefreshTokenValidator:
    def validate(self, *, token_obj: Optional[RefreshToken]):
        """
        전달받은 RefreshToken 객체의 유효성을 검사합니다. (DB 조회 X)
        - 토큰 객체가 존재하는지
        - 토큰이 만료되지 않았는지
        실패 시 AuthenticationError를 발생시킵니다.
        """
        if not token_obj:
            raise AuthenticationError("Refresh token not found or already revoked.")

        if token_obj.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token has expired.")

        # is_revoked는 get_by_token 쿼리에서 이미 필터링되므로, 
        # 여기까지 왔다는 것은 is_revoked=False 라는 의미입니다.
        # 따라서 별도의 is_revoked 체크는 필요하지 않습니다.


refresh_token_validator = RefreshTokenValidator()