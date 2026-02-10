import logging
import hvac
import os # [추가] 파일 존재 여부 확인용
from typing import Optional, List, Dict
from datetime import datetime

from app.core.config import Settings

logger = logging.getLogger(__name__)

class VaultCertificateQueryRepository:
    """
    Vault PKI Secrets Engine과 직접 상호작용하여 인증서 정보를 조회(read)하는
    '읽기' 관련 작업을 담당하는 리포지토리입니다.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._init_vault_client()

    def _init_vault_client(self) -> hvac.Client:
        """
        Vault 클라이언트를 초기화합니다.
        우선적으로 Vault Agent가 배달한 토큰 파일을 사용하고, 실패 시 AppRole 인증을 시도합니다.
        """
        logger.info(f"Initializing Vault client for query repository at {self.settings.VAULT_ADDR}")
        client = hvac.Client(url=self.settings.VAULT_ADDR)

        # 1. [핵심] 비서(Agent)가 두고 간 토큰 파일 확인
        token_path = "/app/temp_certs/token.txt"
        
        if os.path.exists(token_path):
            try:
                with open(token_path, "r") as f:
                    agent_token = f.read().strip()
                if agent_token:
                    client.token = agent_token
                    logger.info("Query Repository: Authenticated using Vault Agent token file.")
                    return client
            except Exception as e:
                logger.warning(f"Failed to read Agent token file in Query Repo: {e}")

        # 2. [백업] 파일이 없으면 기존 AppRole 방식으로 시도
        try:
            role_id = self.settings.VAULT_APPROLE_ROLE_ID
            secret_id = self.settings.VAULT_APPROLE_SECRET_ID

            if not role_id or not secret_id:
                raise ValueError("VAULT_APPROLE_ROLE_ID or VAULT_APPROLE_SECRET_ID not set.")

            logger.info("Query Repository attempting AppRole login (Fallback)...")
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
                serial=serial_number
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
        """
        logger.debug(f"Listing certificates for role: {role_name}")
        try:
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
        현재 Vault에 발급된 서버 MQTT 클라이언트 인증서 중 유효한 것을 조회합니다. (Placeholder)
        """
        logger.warning("get_valid_server_certificate method is a placeholder and not fully implemented yet.")
        return None

# --- Singleton Instance ---
app_settings = Settings()
vault_certificate_query_repository = VaultCertificateQueryRepository(settings=app_settings)