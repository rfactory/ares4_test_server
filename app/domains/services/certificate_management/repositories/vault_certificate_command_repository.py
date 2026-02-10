import logging
import uuid
import hvac
import os
from typing import Optional, Dict, Any, TypedDict
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.objects.user import User
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class VaultCertData(TypedDict):
    """IDE가 함수의 반환 구조를 이해할 수 있도록 정의한 타입입니다."""
    certificate: str
    private_key: str
    issuing_ca: str
    serial_number: str

class VaultCertificateCommandRepository:
    """
    Vault PKI Secrets Engine과 직접 상호작용하여 인증서를 발급/폐기하는 리포지토리입니다.
    보안 규격(.device.ares4.internal)을 엄격히 준수합니다.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._init_vault_client()

    def _init_vault_client(self) -> hvac.Client:
        """Vault Agent 토큰 우선, AppRole 백업 방식으로 인증합니다."""
        client = hvac.Client(url=self.settings.VAULT_ADDR)
        token_path = "/app/temp_certs/token.txt"
        
        if os.path.exists(token_path):
            try:
                with open(token_path, "r") as f:
                    agent_token = f.read().strip()
                if agent_token:
                    client.token = agent_token
                    logger.info("Command Repository: Authenticated via Vault Agent.")
                    return client
            except Exception as e:
                logger.warning(f"Failed to read Agent token: {e}")

        try:
            login_response = client.auth.approle.login(
                role_id=self.settings.VAULT_APPROLE_ROLE_ID,
                secret_id=self.settings.VAULT_APPROLE_SECRET_ID
            )
            client.token = login_response['auth']['client_token']
            logger.info("Command Repository: Authenticated via AppRole.")
            return client
        except Exception as e:
            logger.error(f"Vault authentication critical failure: {e}")
            raise ConnectionError(f"Vault Auth Error: {e}")

    def create_device_certificate(self, db: Session, *, common_name: str, actor_user: Optional[User] = None) -> VaultCertData:
        """
        인자로 받은 common_name(Device UUID)을 사용하여 보안 규격에 맞는 인증서를 발급합니다.
        상위 계층에서 'common_name'이라는 키워드로 인자를 넘겨주므로 이름을 통일합니다.
        """
        # ✅ 전달받은 UUID(common_name) 뒤에 보안 도메인을 붙여 최종 CN 구성
        full_common_name = f"{common_name}.device.ares4.internal"
        logger.info(f"🚀 Issuing device cert for CN: {full_common_name}")
        
        try:
            cert_response = self.client.secrets.pki.generate_certificate(
                # ✅ 1. mount_point를 반드시 명시 (pki_int)
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT, 
                # ✅ 2. env에서 가져온 정확한 Role 이름 사용
                name=self.settings.VAULT_PKI_LISTENER_ROLE,
                common_name=full_common_name,
                extra_params={"ttl": "8760h"}
            )
            
            cert_data: VaultCertData = cert_response['data']
            
            # 감사 로그 기록
            audit_command_provider.log(
                db=db, 
                actor_user=actor_user,
                event_type="DEVICE_CERTIFICATE_CREATED",
                description=f"Issued device certificate for CN='{full_common_name}'.",
                details={
                    "common_name": full_common_name,
                    "serial_number": cert_data.get("serial_number"),
                }
            )
            return cert_data
            
        except Exception as e:
            logger.error(f"💥 Failed to issue cert for {full_common_name}: {e}")
            raise

    def issue_server_mqtt_cert(self, db: Session, *, actor_user: Optional[User] = None) -> Dict[str, Any]:
        """서버용 MQTT 클라이언트 인증서를 발급합니다."""
        common_name = self.settings.MQTT_CLIENT_ID 
        try:
            cert_response = self.client.secrets.pki.generate_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                name="ares-server-mqtt-client-role", 
                common_name=common_name
            )

            audit_command_provider.log(
                db=db,
                actor_user=actor_user,
                event_type="SERVER_MQTT_CERTIFICATE_ISSUED",
                description=f"Issued server MQTT cert for CN='{common_name}'.",
                details={
                    "common_name": common_name,
                    "serial_number": cert_response['data'].get("serial_number"),
                }
            )
            return cert_response['data']
        except Exception as e:
            logger.error(f"Failed to issue server cert: {e}")
            raise

    def revoke_certificate(self, db: Session, *, serial_number: str, actor_user: Optional[User]) -> bool:
        """인증서 폐기"""
        try:
            self.client.secrets.pki.revoke_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                serial_number=serial_number
            )
            audit_command_provider.log(
                db=db, 
                actor_user=actor_user,
                event_type="CERTIFICATE_REVOKED",
                description=f"Revoked cert: {serial_number}.",
                details={ "serial_number": serial_number }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to revoke cert {serial_number}: {e}")
            raise

# 싱글톤 인스턴스
from app.core.config import settings as app_settings
vault_certificate_command_repository = VaultCertificateCommandRepository(settings=app_settings)