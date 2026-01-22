from datetime import datetime

from sqlalchemy import Column, BigInteger, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base
from ..base_model import TimestampMixin # TimestampMixin 임포트

class RefreshToken(Base, TimestampMixin): # TimestampMixin 상속
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
