from sqlalchemy.orm import Session
from datetime import datetime
from app.models.objects.provisioning_token import ProvisioningToken

class ProvisioningTokenCommandCRUD:
    def create(self, db: Session, token_value: str, system_unit_id: int, expires_at: datetime) -> ProvisioningToken:
        """
        [Ticket Issue] QR 토큰 생성
        - 발급자(User/Org) 정보 없이, 오직 '어떤 유닛의 열쇠인가'만 저장합니다.
        """
        obj = ProvisioningToken(
            token_value=token_value,
            system_unit_id=system_unit_id,
            expires_at=expires_at,
            is_used=False
        )
        db.add(obj)
        db.flush()
        return obj

    def mark_as_used(self, db: Session, token: ProvisioningToken):
        """
        [Ticket Validate] 토큰 사용 처리
        - 누가 사용했는지는 기록하지 않습니다 (SystemUnitAssignment가 담당).
        - 토큰을 '사용됨(is_used)' 처리하고 '사용 시점(used_at)'을 남겨 재사용을 막습니다.
        """
        token.is_used = True
        token.used_at = datetime.now()
        db.add(token)
        db.flush()

# 싱글톤 인스턴스
provisioning_token_command_crud = ProvisioningTokenCommandCRUD()