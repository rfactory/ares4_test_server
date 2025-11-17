import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # --- Core Settings ---
    PROJECT_NAME: str = "Ares4 Server v2"
    API_V1_STR: str = "/api/v1"

    # --- Database Settings ---
    DATABASE_URL: str

    # --- JWT Settings ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- MQTT Settings ---
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int = 8883
    MQTT_USERNAME: str
    MQTT_PASSWORD: str
    MQTT_CLIENT_ID: str = "ares-server-v2"
    MQTT_KEEPALIVE: int = 60
    MQTT_CA_CERTS: Optional[str] = None
    MQTT_CLIENT_CERT: Optional[str] = None
    MQTT_CLIENT_KEY: Optional[str] = None

    # --- Email Settings ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
