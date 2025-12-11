import logging
import hvac
from typing import Optional, List, Dict
from datetime import datetime

from app.core.config import Settings

logger = logging.getLogger(__name__)

class VaultCertificateQueryRepository:
    """
    Vault PKI Secrets Engine과 직접 상호작용하여 인증서 정보를 조회(read)하는
    '읽기' 관련 작업을 담당하는 리포지토리입니다.
    민감한 인증서 정보를 조회하는 작업 또한 중요한 보안 이벤트이므로,
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
        logger.info(f"Initializing Vault client for query repository at {self.settings.VAULT_ADDR}")
        client = hvac.Client(url=self.settings.VAULT_ADDR)

        try:
            role_id = self.settings.VAULT_APPROLE_ROLE_ID
            secret_id = self.settings.VAULT_APPROLE_SECRET_ID

            if not role_id or not secret_id:
                raise ValueError("VAULT_APPROLE_ROLE_ID or VAULT_APPROLE_SECRET_ID not set.")

            logger.info("Query Repository attempting AppRole login...")
            login_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            client.token = login_response['auth']['client_token']
            logger.info("Query Repository Vault client authenticated successfully using AppRole.")
        except Exception as e:
            logger.error(f"Query Repository AppRole authentication failed: {e}")
            raise ConnectionError(f"Query Repository Vault AppRole authentication failed: {e}")

        return client

    def get_certificate_by_serial(self, serial_number: str) -> Optional[Dict]:
        """
        주어진 시리얼 번호에 해당하는 인증서의 상세 정보를 Vault에서 조회합니다.

        Args:
            serial_number: 조회할 인증서의 고유 시리얼 번호입니다.

        Returns:
            Vault로부터 받은 인증서 데이터(인증서, 개인 키, 시리얼 번호 등)가 포함된 딕셔너리.
            인증서를 찾을 수 없으면 None을 반환합니다.
        """
        logger.debug(f"Getting certificate details for serial number: {serial_number}")
        try:
            read_response = self.client.secrets.pki.read_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                serial_number=serial_number
            )
            return read_response['data'] if read_response and read_response['data'] else None
        except hvac.exceptions.VaultError as ve:
            if ve.status_code == 404:
                logger.debug(f"Certificate with serial number {serial_number} not found in Vault.")
                return None
            logger.error(f"Vault error getting certificate {serial_number}: {ve}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to get certificate {serial_number}: {e}", exc_info=True)
            raise

    def list_certificates_by_role(self, role_name: str) -> List[str]:
        """
        특정 역할(role_name)로 발급된 모든 인증서의 시리얼 번호 목록을 Vault에서 조회합니다.
        주의: Vault의 list_certificates API는 mount_point에 발급된 모든 시리얼을 반환하므로,
        실제 역할별 필터링은 호출하는 쪽에서 처리해야 할 수 있습니다.

        Args:
            role_name: 조회할 인증서 역할의 이름입니다.

        Returns:
            해당 역할로 발급된 인증서 시리얼 번호 목록.
        """
        logger.debug(f"Listing certificates for role: {role_name}")
        try:
            # list_certificates API는 특정 역할로 필터링하는 기능을 직접 제공하지 않습니다.
            # 여기서는 mount_point에 발급된 모든 인증서 시리얼을 가져옵니다.
            # 역할별 필터링이 필요하면, 서비스 계층에서 추가 로직이 필요합니다.
            list_response = self.client.secrets.pki.list_certificates(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
            )
            return list_response['data']['keys'] if list_response and list_response['data'] and 'keys' in list_response['data'] else []
        except Exception as e:
            logger.error(f"Failed to list certificates for role {role_name}: {e}", exc_info=True)
            raise

    def get_crl(self) -> str:
        """
        Vault의 현재 유효한 인증서 폐기 목록(CRL)을 PEM 형식 문자열로 가져옵니다.

        Returns:
            PEM 형식의 CRL 문자열.
        """
        logger.debug("Getting CRL from Vault")
        try:
            crl_response = self.client.secrets.pki.read_crl(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT
            )
            return crl_response['data']['crl'] if crl_response and crl_response['data'] and 'crl' in crl_response['data'] else ""
        except Exception as e:
            logger.error(f"Failed to get CRL from Vault: {e}", exc_info=True)
            raise

    def get_valid_server_certificate(self) -> Optional[Dict]:
        """
        현재 Vault에 발급된 서버 MQTT 클라이언트 인증서 중 유효하고
        폐기되지 않은 가장 최근의 인증서 정보를 조회합니다.
        주의: Vault PKI API는 특정 CN/Role로 발급된 인증서를 직접 조회하는 기능을 제공하지 않습니다.
        따라서 모든 인증서를 읽어서 필터링하는 방식은 비효율적일 수 있습니다.
        이 메서드는 주로 'Query' 목적으로 Vault에 등록된 모든 인증서를 대상으로 하므로,
        이름이 아닌 시리얼 번호를 기준으로 상세 조회하는 것이 일반적입니다.
        하지만, 여기서는 '현재 유효한 서버 인증서'를 찾는 목적이므로, 
        list -> read -> filter 과정을 거쳐야 합니다. 현재로서는 구현하지 않고 Placeholder로 둡니다.
        """
        logger.warning("get_valid_server_certificate method is a placeholder and not fully implemented yet.")
        # Placeholder implementation - needs actual logic to list, read, and filter
        return None

# --- Singleton Instance ---
app_settings = Settings()
vault_certificate_query_repository = VaultCertificateQueryRepository(settings=app_settings)
