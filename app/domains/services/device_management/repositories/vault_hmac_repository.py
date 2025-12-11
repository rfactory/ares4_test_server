import logging
import hvac

from app.core.config import Settings

logger = logging.getLogger(__name__)

class VaultHmacRepository:
    """
    Vault Transit Engine과의 상호작용을 통해 HMAC 키를 생성하고 검증하는 리포지토리입니다.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._init_vault_client()

    def _init_vault_client(self) -> hvac.Client:
        """Vault 클라이언트를 초기화하고 AppRole으로 인증합니다."""
        logger.info(f"Initializing Vault client for HMAC repository at {self.settings.VAULT_ADDR}")
        client = hvac.Client(url=self.settings.VAULT_ADDR)

        try:
            role_id = self.settings.VAULT_APPROLE_ROLE_ID
            secret_id = self.settings.VAULT_APPROLE_SECRET_ID

            if not role_id or not secret_id:
                raise ValueError("VAULT_APPROLE_ROLE_ID or VAULT_APPROLE_SECRET_ID not set.")

            logger.info("HMAC Repository attempting AppRole login...")
            login_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            client.token = login_response['auth']['client_token']
            logger.info("HMAC Repository Vault client authenticated successfully using AppRole.")
        except Exception as e:
            logger.error(f"HMAC Repository AppRole authentication failed: {e}")
            raise ConnectionError(f"HMAC Repository Vault AppRole authentication failed: {e}")

        return client

    def create_hmac_key(self, device_id: str) -> str:
        """
        주어진 device_id에 대해 Vault Transit Engine에 HMAC 키를 생성합니다.
        키 이름은 'device-hmac-{device_id}' 형식을 따릅니다.
        """
        key_name = f"device-hmac-{device_id}"
        logger.info(f"Creating HMAC key '{key_name}' in Vault Transit Engine.")
        try:
            self.client.secrets.transit.create_key(
                name=key_name,
                key_type="hmac-sha256", # 'type' 대신 'key_type' 사용
                allow_plaintext_backup=False
            )
            return key_name  # DB에 이 key_name만 저장
        except Exception as e:
            logger.error(f"Failed to create HMAC key '{key_name}' in Vault: {e}", exc_info=True)
            raise

    def verify_hmac(self, key_name: str, payload: str, signature: str) -> bool:
        """
        Vault Transit Engine을 사용하여 HMAC 서명을 검증합니다.
        """
        logger.debug(f"Verifying HMAC for key '{key_name}' with Vault Transit Engine.")
        try:
            response = self.client.secrets.transit.verify_hmac( # 'verify' 대신 'verify_hmac' 사용
                name=key_name,
                hmac=signature, # 'hmac' 파라미터 이름 확인
                hash_algorithm="sha256", # 해시 알고리즘 명시
                input=payload # 'input' 파라미터 이름 확인
            )
            return response["data"]["valid"]
        except Exception as e:
            logger.error(f"HMAC verification failed for key '{key_name}' with Vault: {e}", exc_info=True)
            return False # 검증 실패 시 False 반환

# --- Singleton Instance ---
# 애플리케이션 설정(settings)을 로드하여 리포지토리의 싱글턴 인스턴스를 생성합니다.
app_settings = Settings()
vault_hmac_repository = VaultHmacRepository(settings=app_settings)
