import logging
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

# 실제 명령 발행을 담당하는 Repository와 Manager를 가져옵니다.
from app.domains.services.command_dispatch.repositories.command_dispatch_repository import CommandDispatchRepository
from app.domains.services.command_dispatch.managers.mqtt_connection_manager import MqttConnectionManager
from app.core.config import settings

logger = logging.getLogger(__name__)

class MqttCommandProvider:
    """
    내부 도메인(예: 헬스 체커)에서 MQTT 명령을 기기나 앱으로 
    직접 발행할 수 있게 해주는 도메인 간 브릿지입니다.
    """
    def __init__(self):
        # 발행 전용 커넥션 매니저와 리포지토리를 준비합니다.
        # client_id에 난수를 섞어 중복 연결을 방지하는 로직이 Manager 내부에 있습니다.
        self._connection_manager = MqttConnectionManager(settings, client_id="ares-server-internal-pub")
        self._repository = CommandDispatchRepository(settings, self._connection_manager)

    def publish_command(
        self, 
        db: Session, 
        *, 
        topic: str, 
        command: Dict, 
        actor_user: Optional[Any] = None # 행위자가 시스템일 경우 None이 가능합니다.
    ):
        """
        주어진 토픽으로 MQTT 메시지를 발행합니다. 
        감사 로그(Audit Log)는 Repository 내부에서 자동으로 기록됩니다.
        """
        # 주의: 실제 배포 환경에서는 앱 시작 시 _connection_manager.connect()가 
        # 비동기로 완료된 상태여야 발행이 가능합니다.
        
        return self._repository.publish_command(
            db=db,
            topic=topic,
            command=command,
            actor_user=actor_user
        )

# 싱글턴으로 제공하여 어디서든 접근 가능하게 합니다.
mqtt_command_provider = MqttCommandProvider()