import logging
import hvac
import os

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
        """Vault 클라이언트를 초기화합니다. 에이전트 토큰을 우선 사용하고, 없으면 AppRole로 시도합니다."""
        logger.info(f"Initializing Vault client at {self.settings.VAULT_ADDR}")
        client = hvac.Client(url=self.settings.VAULT_ADDR)

        # 1. 먼저 Vault Agent가 배달해 준 토큰 파일이 있는지 확인합니다.
        token_path = "/app/temp_certs/token.txt"
        try:
            if os.path.exists(token_path):
                with open(token_path, "r") as f:
                    client.token = f.read().strip()
                logger.info("Authenticated using Vault Agent token file.")
                return client
        except Exception as e:
            logger.warning(f"Failed to read Vault Agent token: {e}. Falling back to AppRole.")

        # 2. 토큰 파일이 없다면 기존 AppRole 방식으로 시도합니다. (하위 호환성 유지)
        try:
            role_id = self.settings.VAULT_APPROLE_ROLE_ID
            secret_id = self.settings.VAULT_APPROLE_SECRET_ID

            if role_id and secret_id:
                login_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
                client.token = login_response['auth']['client_token']
                logger.info("Authenticated successfully using AppRole login.")
            else:
                raise ValueError("Neither Agent token nor AppRole credentials available.")
        except Exception as e:
            logger.error(f"All Vault authentication methods failed: {e}")
            raise ConnectionError(f"Vault authentication failed: {e}")

        return client
    
    def store_hmac(self, path: str, key: str):
        """
        [추가] KV Engine을 사용하여 생성된 HMAC 키를 특정 경로에 저장합니다.
        Policy에서 'ares4/hmac/serial' 경로에 저장할 때 사용합니다.
        """
        logger.info(f"Storing HMAC key at Vault path: {path}")
        try:
            # KV V2 엔진 기준 저장 (mount_point는 설정에 따라 'secret' 등으로 변경 가능)
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=dict(hmac_key=key)
            )
        except Exception as e:
            logger.error(f"Failed to store HMAC key at {path}: {e}")
            raise

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
            response = self.client.secrets.transit.verify( # 'verify' 대신 'verify_hmac' 사용
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
