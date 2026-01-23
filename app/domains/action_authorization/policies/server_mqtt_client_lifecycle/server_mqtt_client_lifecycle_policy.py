import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.core.registry import app_registry
from app.domains.services.command_dispatch.managers.mqtt_connection_manager import MqttConnectionManager
from app.domains.services.command_dispatch.repositories.command_dispatch_repository import CommandDispatchRepository
from app.domains.inter_domain.policies.server_certificate_acquisition.server_certificate_acquisition_policy import server_certificate_acquisition_policy_provider

logger = logging.getLogger(__name__)

class ServerMqttClientLifecyclePolicy:
    """
    애플리케이션의 생명주기(lifespan) 동안 MQTT 클라이언트들의
    전체 생명주기를 조율(orchestrate)하는 최상위 Policy입니다.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.publisher_manager: Optional[MqttConnectionManager] = None

    async def start_publisher_client(self, db: Session):
        """
        Publisher용 MQTT 클라이언트의 생명주기를 시작합니다.
        1. 유효한 인증서 획득
        2. Connection Manager 생성 및 인증서 주입
        3. Repository 생성 및 레지스트리 등록
        4. Connection Manager 연결 시작
        """
        logger.info("Starting MQTT Publisher client lifecycle...")
        try:
            # 1. Acquire a valid certificate for the publisher
            logger.info("Acquiring certificate for MQTT publisher...")
            cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(db, current_cert_data=None)
            
            # 2. Create Connection Manager and inject the certificate
            logger.info("Initializing MqttConnectionManager for publisher...")
            self.publisher_manager = MqttConnectionManager(
                settings=self.settings,
                client_id=self.settings.MQTT_CLIENT_ID
            )
            self.publisher_manager.set_certificate_data(cert_data)
            
            # 3. Create CommandDispatchRepository and register it
            logger.info("Initializing and registering CommandDispatchRepository...")
            command_dispatch_repo = CommandDispatchRepository(
                settings=self.settings,
                connection_manager=self.publisher_manager
            )
            app_registry.command_dispatch_repository = command_dispatch_repo
            
            # 4. Start the connection
            # [수정] MqttConnectionManager.connect()는 비동기 함수이므로 await를 추가합니다.
            await self.publisher_manager.connect()
            logger.info("MQTT Publisher client lifecycle started successfully.")
        except Exception as e:
            logger.critical(f"Failed to start MQTT Publisher client lifecycle: {e}", exc_info=True)
            raise

    async def stop_publisher_client(self):
        """
        Publisher용 MQTT 클라이언트의 생명주기를 중지합니다.
        """
        logger.info("Stopping MQTT Publisher client lifecycle...")
        if self.publisher_manager:
            # [수정] MqttConnectionManager.disconnect()는 비동기 함수이므로 await를 추가합니다.
            await self.publisher_manager.disconnect()
            logger.info("MQTT Publisher client lifecycle stopped.")

# Singleton instance
server_mqtt_client_lifecycle_policy = ServerMqttClientLifecyclePolicy(settings=Settings())