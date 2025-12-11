import logging
import json
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.objects.user import User
from app.domains.services.command_dispatch.managers.mqtt_connection_manager import MqttConnectionManager
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class CommandDispatchRepository:
    """
    MQTT를 통해 기기로 명령(Command)을 발행(publish)하는 역할을 담당합니다.
    발행되는 모든 명령에 대해 감사 로그를 기록합니다.
    """
    def __init__(self, settings: Settings, connection_manager: MqttConnectionManager):
        self.settings = settings
        self.connection_manager = connection_manager

    def publish_command(self, db: Session, *, topic: str, command: Dict, actor_user: Optional[User]):
        """
        주어진 토픽으로 명령 메시지를 발행하고 감사 로그를 기록합니다.

        Args:
            db: 감사 로그 기록에 필요한 데이터베이스 세션입니다.
            topic: 명령을 발행할 MQTT 토픽입니다.
            command: 발행할 명령 내용 (JSON으로 변환될 딕셔너리).
            actor_user: 이 명령을 내린 사용자 객체입니다.
        """
        if not self.connection_manager.is_connected:
            logger.error(f"Cannot publish command to topic '{topic}'. MQTT client is not connected.")
            # In a real scenario, you might want to raise a specific exception here.
            return

        try:
            # Convert command dict to JSON string
            message = json.dumps(command)

            # Use the client from the connection manager to publish
            if self.connection_manager.client:
                self.connection_manager.client.publish(topic, message, qos=1)
            else:
                logger.error("MQTT client is not initialized.")
                return

            # Log the audit event for dispatching a command
            audit_command_provider.log(
                db=db,
                actor_user=actor_user,
                event_type="DEVICE_COMMAND_DISPATCHED",
                description=f"Dispatched command to topic: {topic}",
                details={
                    "topic": topic,
                    "command": command
                }
            )
            logger.info(f"Successfully published command to topic '{topic}' and logged audit event.")
        except Exception as e:
            logger.error(f"Failed to publish command to topic '{topic}': {e}", exc_info=True)
            raise

# 이 리포지토리는 Policy 또는 애플리케이션 시작 시 인스턴스화되며,
# MqttConnectionManager 인스턴스를 주입받아 사용합니다.
# 자체적으로 싱글턴이 아니며, 관리되는 MqttConnectionManager에 의존합니다.