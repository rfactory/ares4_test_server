import os
import logging
from typing import Optional, Any
from pydantic import root_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.vault_client import VaultClient

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # --- Core Settings ---
    PROJECT_NAME: str = "Ares4 Server v2"
    API_V1_STR: str = "/api/v1"

    # --- Vault Settings (used by VaultClient) ---
    VAULT_ADDR: Optional[str] = None
    VAULT_TOKEN: Optional[str] = None

    # --- Database Settings (will be loaded from Vault) ---
    DATABASE_URL: Optional[str] = None

    # --- JWT Settings (will be loaded from Vault) ---
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- MQTT Settings ---
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int = 8883
    MQTT_USERNAME: str
    MQTT_PASSWORD: Optional[str] = None # Will be loaded from Vault
    MQTT_CLIENT_ID: str = "ares-server-v2"
    MQTT_KEEPALIVE: int = 60
    MQTT_CA_CERT_CONTENT: Optional[str] = None
    MQTT_CLIENT_CERT_CONTENT: Optional[str] = None
    MQTT_CLIENT_KEY_CONTENT: Optional[str] = None

    # --- Email Settings (will be loaded from Vault) ---
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_SERVER: Optional[str] = None
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # This model_config tells Pydantic to load settings from a .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @root_validator(pre=True)
    def _load_secrets_from_vault(cls, values):
        # This method is called before Pydantic's main validation
        vault_client_instance = VaultClient.get_client()
        if not vault_client_instance:
            logger.warning("Vault client not initialized. Relying on environment variables for all secrets.")
            return values

        logger.info("Attempting to load secrets from Vault...")

        # Database URL
        db_secret = VaultClient.read_secret(path="db", key="connection_string")
        if db_secret: values['DATABASE_URL'] = db_secret
        
        # JWT Secret Key
        jwt_secret = VaultClient.read_secret(path="jwt", key="secret_key")
        if jwt_secret: values['JWT_SECRET_KEY'] = jwt_secret

        # MQTT Password
        mqtt_password = VaultClient.read_secret(path="mqtt/users/ares_user", key="password")
        if mqtt_password: values['MQTT_PASSWORD'] = mqtt_password

        # MQTT Certificates
        if VaultClient.read_secret(path="mqtt/certs", key="ca_crt") is not None:
            values['MQTT_CA_CERT_CONTENT'] = VaultClient.read_secret(path="mqtt/certs", key="ca_crt")
            values['MQTT_CLIENT_CERT_CONTENT'] = VaultClient.read_secret(path="mqtt/certs", key="client_crt")
            values['MQTT_CLIENT_KEY_CONTENT'] = VaultClient.read_secret(path="mqtt/certs", key="client_key")
            logger.info("Successfully loaded MQTT certificate contents from Vault.")
        else:
            logger.warning("MQTT certificate contents not found in Vault. Check if they need to be set via env.")

        # Email Credentials
        if VaultClient.read_secret(path="email", key="username") is not None:
            values['MAIL_USERNAME'] = VaultClient.read_secret(path="email", key="username")
            values['MAIL_PASSWORD'] = VaultClient.read_secret(path="email", key="password")
            values['MAIL_FROM'] = VaultClient.read_secret(path="email", key="from")
            values['MAIL_PORT'] = int(VaultClient.read_secret(path="email", key="port"))
            values['MAIL_SERVER'] = VaultClient.read_secret(path="email", key="server")
            logger.info("Successfully loaded email credentials from Vault.")
        else: 
            logger.warning("Email credentials not found in Vault. Check if they need to be set via env.")

        logger.info("Finished attempting to load secrets from Vault.")
        return values

settings = Settings()
