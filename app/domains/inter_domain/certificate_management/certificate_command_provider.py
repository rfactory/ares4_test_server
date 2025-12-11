from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.domains.services.certificate_management.repositories.vault_certificate_command_repository import vault_certificate_command_repository

class CertificateCommandProvider:
    """
    `certificate_management` 도메인의 Command Repository 기능을 외부 도메인에 노출하는 제공자입니다.
    `Service` 계층이 생략되었으므로, `Repository`를 직접 호출합니다.
    """
    def create_device_certificate(self, db: Session, *, common_name: str, actor_user: Optional[User]) -> Dict:
        """
        새로운 장치 인증서를 발급하고 감사 로그를 기록합니다.
        """
        return vault_certificate_command_repository.create_device_certificate(db, common_name=common_name, actor_user=actor_user)

    def issue_server_mqtt_cert(self, db: Session, *, actor_user: Optional[User] = None) -> Dict:
        """
        서버 자신(MQTT 클라이언트)을 위한 새로운 인증서를 발급하고 감사 로그를 기록합니다。
        """
        return vault_certificate_command_repository.issue_server_mqtt_cert(db, actor_user=actor_user)

    def revoke_certificate(self, db: Session, *, serial_number: str, actor_user: Optional[User]) -> bool:
        """
        주어진 시리얼 번호에 해당하는 인증서를 Vault에서 폐기하고 감사 로그를 기록합니다。
        """
        return vault_certificate_command_repository.revoke_certificate(db, serial_number=serial_number, actor_user=actor_user)

certificate_command_provider = CertificateCommandProvider()