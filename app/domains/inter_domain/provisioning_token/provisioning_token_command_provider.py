from sqlalchemy.orm import Session
from app.domains.services.provisioning_token.services.provisioning_token_command_service import provisioning_token_command_service

class ProvisioningTokenCommandProvider:
    """
    [Inter-Domain Provider] 
    프로비저닝 토큰 도메인의 상태 변경 기능을 외부(Policy 등)에 제공합니다.
    """

    def mark_as_used(self, db: Session, token_id: int):
        """
        토큰 사용 완료 처리를 위해 서비스를 호출합니다. 
        (모델 수정에 따라 used_by_user_id 인자는 제거되었습니다.)
        """
        provisioning_token_command_service.use_token(db, token_id)

# 싱글톤 인스턴스
provisioning_token_command_provider = ProvisioningTokenCommandProvider()