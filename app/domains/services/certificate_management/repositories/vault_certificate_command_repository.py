import logging
import hvac
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.objects.user import User
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class VaultCertificateCommandRepository:
    """
    Vault PKI Secrets Engine과 직접 상호작용하여 인증서를 생성(issue)하거나
    폐기(revoke)하는 '쓰기' 관련 작업을 담당하는 리포지토리입니다.
    이 리포지토리의 각 메서드는 중요한 상태 변경을 유발하므로,
    프로젝트의 아키텍처 패턴에 따라 자체적으로 감사 로그를 기록할 책임을 가집니다.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._init_vault_client()

    def _init_vault_client(self) -> hvac.Client:
        """
        Vault 클라이언트를 초기화하고, 설정에 명시된 AppRole ID와 Secret ID를 사용하여 인증합니다.
        성공적으로 인증되면, 클라이언트 토큰이 설정됩니다.
        실패 시, ConnectionError를 발생시켜 애플리케이션 시작을 중단시킬 수 있습니다.
        """
        logger.info(f"Initializing Vault client for command repository at {self.settings.VAULT_ADDR}")
        client = hvac.Client(url=self.settings.VAULT_ADDR)

        try:
            role_id = self.settings.VAULT_APPROLE_ROLE_ID
            secret_id = self.settings.VAULT_APPROLE_SECRET_ID

            if not role_id or not secret_id:
                raise ValueError("VAULT_APPROLE_ROLE_ID or VAULT_APPROLE_SECRET_ID not set.")

            logger.info("Command Repository attempting AppRole login...")
            login_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            client.token = login_response['auth']['client_token']
            logger.info("Command Repository Vault client authenticated successfully using AppRole.")
        except Exception as e:
            logger.error(f"Command Repository AppRole authentication failed: {e}")
            raise ConnectionError(f"Command Repository Vault AppRole authentication failed: {e}")

        return client

    def create_device_certificate(self, db: Session, *, common_name: str, actor_user: Optional[User]) -> Dict:
        """
        주어진 common_name(Device UUID)에 대해 새로운 장치 인증서를 발급하고 감사 로그를 기록합니다.

        Args:
            db: 감사 로그 기록에 필요한 데이터베이스 세션입니다.
            common_name: 인증서의 주체 이름(Common Name)으로, 장치의 UUID가 사용됩니다.
            actor_user: 이 행위를 수행한 사용자 객체입니다. 감사 로그에 기록됩니다.

        Returns:
            Vault로부터 받은 인증서 데이터(인증서, 개인 키, 시리얼 번호 등)가 포함된 딕셔너리.
        """
        logger.info(f"Issuing new device certificate for CN='{common_name}'")
        try:
            # 'ares-server-role'은 Vault에 미리 정의된, 장치 인증서 발급 권한을 가진 역할입니다.
            cert_response = self.client.secrets.pki.generate_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                name="ares-server-role", 
                common_name=common_name
            )
            
            # 인증서 발급은 중요한 보안 이벤트이므로, 감사 로그를 기록합니다.
            audit_command_provider.log(
                db=db, 
                actor_user=actor_user,
                event_type="DEVICE_CERTIFICATE_CREATED",
                description=f"Issued new device certificate for CN='{common_name}'.",
                details={
                    "common_name": common_name,
                    "serial_number": cert_response['data'].get("serial_number"),
                    "issuing_ca": cert_response['data'].get("issuing_ca"),
                }
            )
            return cert_response['data']
        except Exception as e:
            logger.error(f"Failed to issue device certificate for CN='{common_name}': {e}", exc_info=True)
            raise

    def issue_server_mqtt_cert(self, db: Session, *, actor_user: Optional[User] = None) -> Dict:
        """
        서버 자신(MQTT 클라이언트)을 위한 새로운 인증서를 발급하고 감사 로그를 기록합니다.
        
        Args:
            db: 감사 로그 기록에 필요한 데이터베이스 세션입니다.
            actor_user: 이 행위를 수행한 사용자 객체. 시스템 자체의 행위일 경우 None일 수 있습니다.

        Returns:
            Vault로부터 받은 인증서 데이터(인증서, 개인 키, 시리얼 번호 등)가 포함된 딕셔너리.
        """
        common_name = self.settings.MQTT_CLIENT_ID
        try:
            # 'ares-server-mqtt-client-role'은 서버 MQTT 클라이언트를 위해 특별히 정의된 역할입니다.
            cert_response = self.client.secrets.pki.generate_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                name="ares-server-mqtt-client-role", 
                common_name=common_name
            )

            # 서버의 핵심 보안 자격 증명이 생성되는 것이므로, 감사 로그를 기록합니다.
            audit_command_provider.log(
                db=db,
                actor_user=actor_user,
                event_type="SERVER_MQTT_CERTIFICATE_ISSUED",
                description=f"Issued new server MQTT client certificate for CN='{common_name}'.",
                details={
                    "common_name": common_name,
                    "serial_number": cert_response['data'].get("serial_number"),
                    "issuing_ca": cert_response['data'].get("issuing_ca"),
                }
            )
            return cert_response['data']
        except Exception as e:
            logger.error(f"Failed to issue server MQTT client certificate for CN='{common_name}': {e}", exc_info=True)
            raise

    def revoke_certificate(self, db: Session, *, serial_number: str, actor_user: Optional[User]) -> bool:
        """
        주어진 시리얼 번호에 해당하는 인증서를 Vault에서 폐기(revoke)하고 감사 로그를 기록합니다.

        Args:
            db: 감사 로그 기록에 필요한 데이터베이스 세션입니다.
            serial_number: 폐기할 인증서의 고유 시리얼 번호입니다.
            actor_user: 이 행위를 수행한 사용자 객체입니다.

        Returns:
            폐기가 성공적으로 처리되었는지 여부를 나타내는 boolean 값.
        """
        logger.info(f"Revoking certificate with serial number: {serial_number}")
        try:
            revoke_response = self.client.secrets.pki.revoke_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                serial_number=serial_number
            )
            
            # 인증서 폐기는 매우 중요한 보안 이벤트이므로, 반드시 감사 로그를 기록합니다.
            audit_command_provider.log(
                db=db, 
                actor_user=actor_user,
                event_type="CERTIFICATE_REVOKED",
                description=f"Revoked certificate with serial number: {serial_number}.",
                details={ "serial_number": serial_number }
            )
            return revoke_response is not None and 'revocation_time' in revoke_response.get('data', {})
        except Exception as e:
            logger.error(f"Failed to revoke certificate with serial number {serial_number}: {e}", exc_info=True)
            raise

# --- Singleton Instance ---
app_settings = Settings()
vault_certificate_command_repository = VaultCertificateCommandRepository(settings=app_settings)
