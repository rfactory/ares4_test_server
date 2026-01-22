from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger # BigInteger 임포트

from app.core.crud_base import CRUDBase
from app.models.objects.refresh_token import RefreshToken

class CRUDTokenManagementCommand(CRUDBase[RefreshToken, RefreshToken, RefreshToken]):
    def create(self, db: Session, *, user_id: BigInteger, token: str, expires_at: datetime) -> RefreshToken:
        """새로운 Refresh Token 레코드를 생성하지만, 커밋은 하지 않습니다."""
        db_obj = self.model(user_id=user_id, token=token, expires_at=expires_at, is_revoked=False)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def revoke(self, db: Session, *, refresh_token_obj: RefreshToken) -> RefreshToken:
        """주어진 Refresh Token 객체를 폐기 상태로 변경하지만, 커밋은 하지 않습니다."""
        refresh_token_obj.is_revoked = True
        db.add(refresh_token_obj)
        db.flush()
        db.refresh(refresh_token_obj)
        return refresh_token_obj

    def revoke_all_for_user(self, db: Session, *, user_id: BigInteger) -> int:
        """
        특정 사용자의 모든 유효한 RefreshToken을 폐기 처리하고, 폐기된 토큰의 수를 반환합니다.
        커밋은 하지 않습니다.
        """
        num_revoked = db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.is_revoked == False
        ).update({"is_revoked": True}, synchronize_session=False)
        db.flush()
        return num_revoked

token_management_command_crud = CRUDTokenManagementCommand(RefreshToken)
