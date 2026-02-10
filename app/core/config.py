from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # --- Core Settings ---
    PROJECT_NAME: str = "Ares4 Server v2"
    API_V1_STR: str = "/api/v1"

    # --- Database Settings ---
    DATABASE_URL: str

    # --- Redis Settings ---
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # --- JWT Settings ---
    JWT_SECRET_KEYS: str # List[str]에서 str으로 다시 변경
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 5 # 5분으로 변경
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14 # 14일로 설정

    # --- MQTT Settings ---
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int = 8883
    MQTT_USERNAME: str
    MQTT_PASSWORD: str
    MQTT_CLIENT_ID: str # For the FastAPI app publisher
    MQTT_LISTENER_CLIENT_ID: str = "ares4-mqtt-listener"
    MQTT_LISTENER_MAX_WORKERS: int = 10
    MQTT_KEEPALIVE: int = 60
    MQTT_INITIAL_CONNECT_DELAY: int = 60
    MQTT_RECONNECT_DELAY: int = 10
    MQTT_MAX_RETRIES: int = 20
    MQTT_CA_CERTS: Optional[str] = None
    MQTT_CLIENT_CERT: Optional[str] = None
    MQTT_CLIENT_KEY: Optional[str] = None
    MQTT_TLS_ENABLED: bool = True
    MQTT_TLS_INSECURE: bool = False
    
    # --- EMQX Webhook Settings ---
    EMQX_WEBHOOK_SECRET: str
    
    # --- Storage Settings ---
    UPLOAD_DIR: str = "/app/uploads"
    
    # --- Vault Settings ---
    VAULT_ADDR: str
    VAULT_APPROLE_ROLE_ID: Optional[str] = None
    VAULT_APPROLE_SECRET_ID: Optional[str] = None
    VAULT_PKI_MOUNT_POINT: str = "pki_int"
    VAULT_PKI_LISTENER_ROLE: str = "ares-server-role"
    VAULT_SERVER_CERT_TTL: str = "720h" # 서버 MQTT 클라이언트 인증서 유효기간 (예: 30일)

    # --- Health Checker Settings ---
    DEVICE_HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    DEVICE_TIMEOUT_SECONDS: int = 60 # 60 seconds, adjusted based on 10-second telemetry
    REDIS_DEVICE_LAST_SEEN_ZSET_KEY: str = "device_last_seen"

    # --- Email Settings ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # --- Storage Settings ---
    UPLOAD_DIR: str = "/app/uploads"
    
        # --- Invitation Settings ---
    INVITATION_EXPIRATION_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=[".env", "../shared_config/.env"],
        env_file_encoding='utf-8',
        extra='ignore',
        secrets_dir='/run/secrets'
        ) # env_file 추가
    
@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg]

settings = get_settings()
