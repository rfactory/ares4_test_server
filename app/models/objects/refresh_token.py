from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    # 순환 참조 방지를 위해 User 모델 임포트
    from app.models.objects.user import User

class RefreshToken(Base, TimestampMixin):
    """
    [Object] 리프레시 토큰 모델:
    사용자의 로그인 세션을 안전하게 유지하고, 만료되거나 탈취된 토큰을 즉시 무효화(Revoke)합니다.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 토큰 소유자
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True, nullable=False
    )
    
    # 실제 JWT 또는 난수 토큰 값
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    # 보안 관리
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Relationships (Mapped 적용 완료) ---
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, is_revoked={self.is_revoked})>"