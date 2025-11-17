import os
import hvac
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class VaultClient:
    _client = None

    @classmethod
    def get_client(cls) -> Optional[hvac.Client]:
        if cls._client is None:
            vault_addr = os.getenv("VAULT_ADDR")
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_addr or not vault_token:
                logger.warning("VAULT_ADDR or VAULT_TOKEN not set. Vault client will not be initialized.")
                return None

            try:
                client = hvac.Client(url=vault_addr, token=vault_token)
                if client.is_authenticated():
                    cls._client = client
                    logger.info("Vault client initialized and authenticated successfully.")
                else:
                    logger.error("Vault client failed to authenticate. Check VAULT_TOKEN.")
                    cls._client = None
            except Exception as e:
                logger.error(f"Error initializing Vault client: {e}")
                cls._client = None
        return cls._client

    @classmethod
    def read_secret(cls, path: str, key: str) -> Optional[Any]:
        client = cls.get_client()
        if not client:
            return None

        try:
            read_response = client.secrets.kv.v2.read_secret_version(path=path)
            if read_response and 'data' in read_response and 'data' in read_response['data']:
                secret_data = read_response['data']['data']
                if key in secret_data:
                    logger.debug(f"Successfully read secret '{key}' from Vault path '{path}'.")
                    return secret_data[key]
                else:
                    logger.warning(f"Key '{key}' not found in Vault path '{path}'.")
            else:
                logger.warning(f"No data found in Vault path '{path}'.")
        except hvac.exceptions.VaultError as e:
            logger.warning(f"Vault error reading secret from path '{path}', key '{key}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading secret from Vault path '{path}', key '{key}': {e}")
        return None

# Example usage (for testing purposes, not part of the main app flow)
if __name__ == "__main__":
    # Set dummy environment variables for local testing
    os.environ["VAULT_ADDR"] = "http://localhost:8200"
    os.environ["VAULT_TOKEN"] = "root"

    client = VaultClient.get_client()
    if client:
        mqtt_password = VaultClient.read_secret(path="mqtt/users/ares_user", key="password")
        if mqtt_password:
            print(f"MQTT Password from Vault: {mqtt_password}")
        else:
            print("Failed to retrieve MQTT password from Vault.")
    else:
        print("Vault client not initialized.")
