from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.token_generator import token_generator, TokenType
from app.domains.services.provisioning_token.crud.provisioning_token_command_crud import provisioning_token_command_crud
from app.core.exceptions import NotFoundError

class ProvisioningTokenCommandService:
    """
    [Command Service] 프로비저닝 토큰(입장권)의 상태 변경 및 생성을 담당하는 서비스입니다.
    이제 토큰은 특정 주체에 종속되지 않으며, 오직 '입장권'으로서의 유효성만 관리합니다.
    """

    def use_token(self, db: Session, token_id: int):
        """
        토큰을 사용 완료 처리합니다.
        누가 주인이 되었는지는 SystemUnitAssignment가 관리하므로, 
        여기서는 토큰의 상태(is_used)와 사용 시점(used_at)만 업데이트합니다.
        """
        from app.models.objects.provisioning_token import ProvisioningToken
        token = db.query(ProvisioningToken).filter(ProvisioningToken.id == token_id).first()
        
        if not token:
            raise NotFoundError("ProvisioningToken", token_id)
            
        # CRUD 계층의 수정 사항에 맞춰 user_id 인자를 제거하고 호출합니다.
        provisioning_token_command_crud.mark_as_used(db, token)

    def create_provisioning_token(
        self, 
        db: Session, 
        system_unit_id: int, 
        expires_in_hours: int = 24
    ):
        """
        시스템 유닛 등록을 위한 QR 토큰을 생성합니다. 
        Core 레벨의 TokenGenerator를 사용하여 조건에 맞는 안전한 토큰 값을 생성합니다.
        """
        # 1. 토큰 문자열 생성 (URL Safe 방식, 접두사 'qr-' 사용)
        token_value = token_generator.generate(
            length=32, 
            type=TokenType.URL_SAFE, 
            prefix="qr-"
        )
        
        # 2. 만료 시간 설정
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        # 3. CRUD를 호출하여 DB에 익명 토큰 저장
        return provisioning_token_command_crud.create(
            db=db,
            token_value=token_value,
            system_unit_id=system_unit_id,
            expires_at=expires_at
        )

# 싱글톤 인스턴스
provisioning_token_command_service = ProvisioningTokenCommandService()