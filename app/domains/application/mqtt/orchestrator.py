import logging
import asyncio
from typing import Dict, Optional, Callable
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.registry import app_registry
from app.domains.services.command_dispatch.managers.mqtt_connection_manager import MqttConnectionManager
from app.domains.services.command_dispatch.repositories.command_dispatch_repository import CommandDispatchRepository
from app.domains.inter_domain.policies.server_certificate_acquisition.server_certificate_acquisition_policy import server_certificate_acquisition_policy_provider

logger = logging.getLogger(__name__)

class MqttLifecycleOrchestrator:
    """
    애플리케이션의 MQTT 클라이언트들(Publisher, Listener)의 생명주기를 조율하는 컴포넌트입니다.
    `main.py`의 `lifespan` 이벤트에 의해 호출됩니다.
    """
    def __init__(self, settings: Settings, db_session_factory: Callable[..., Session]):
        self.settings = settings
        self.db_session_factory = db_session_factory
        self.publisher_connection_manager: Optional[MqttConnectionManager] = None

    async def startup(self):
        """
        Publisher 클라이언트를 설정하고 시작합니다. (Non-blocking)
        """
        logger.info("MqttLifecycleOrchestrator starting up...")
        with self.db_session_factory() as db:
            try:
                logger.info("Setting up MQTT Publisher client...")
                
                logger.info("Acquiring certificate for MQTT publisher...")
                publisher_cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(
                    db=db, 
                    current_cert_data=None
                )

                logger.info("Initializing MqttConnectionManager for publisher...")
                self.publisher_connection_manager = MqttConnectionManager(
                    settings=self.settings,
                    client_id=self.settings.MQTT_CLIENT_ID
                )
                self.publisher_connection_manager.set_certificate_data(publisher_cert_data)

                logger.info("Initializing and registering CommandDispatchRepository...")
                command_dispatch_repo = CommandDispatchRepository(
                    settings=self.settings,
                    connection_manager=self.publisher_connection_manager
                )
                app_registry.command_dispatch_repository = command_dispatch_repo
                
                # [수정됨] 여기서 await로 기다리지 않고, 백그라운드 태스크로 던집니다.
                # 이렇게 하면 EMQX가 죽어있어도 FastAPI는 정상적으로 켜집니다.
                # [수정됨] EMQX가 웹훅을 완전히 준비할 시간을 벌기 위해 5초 지연을 추가합니다.
                await asyncio.sleep(5)
                logger.info("Initiating MQTT connection in background task...")
                asyncio.create_task(self.publisher_connection_manager.connect())

                db.commit()
            except Exception as e:
                db.rollback()
                logger.critical(f"MqttLifecycleOrchestrator startup failed: {e}", exc_info=True)
                raise

        logger.info("MqttLifecycleOrchestrator startup initiated (Connection in progress).")

    async def shutdown(self):
        """
        MQTT 클라이언트 연결을 해제하고 리소스를 정리합니다.
        """
        logger.info("MqttLifecycleOrchestrator shutting down...")
        if self.publisher_connection_manager:
            await self.publisher_connection_manager.disconnect()
            logger.info("MQTT Publisher client disconnected.")
        logger.info("MqttLifecycleOrchestrator shutdown completed.")

    def is_publisher_connected(self) -> bool:
        """
        Publisher용 MQTT 클라이언트가 현재 브로커에 연결되어 있는지 여부를 반환합니다.
        """
        return self.publisher_connection_manager.is_connected if self.publisher_connection_manager else False