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
        # [수정] 태스크 변수명을 하나로 통일 (_rotation_monitor_task)
        self._rotation_monitor_task: Optional[asyncio.Task] = None
        # [추가] 연결 태스크 가비지 컬렉션 방지를 위한 참조 저장
        self._connect_task: Optional[asyncio.Task] = None
    
    async def _rotation_monitoring_loop(self):
        """
        주기적으로 인증서 상태를 체크하고 로테이션을 지휘합니다.
        """
        logger.info("📡 MQTT Certificate Rotation Monitor Loop started.")
        
        # 초기 대기 시간 (서버 시작 직후에는 갱신할 필요가 없으므로 10분 후부터 체크)
        base_sleep = 600
        
        while True:
            try:
                await asyncio.sleep(base_sleep)
                
                if not self.publisher_connection_manager:
                    continue
                
                logger.info("🔍 Checking MQTT certificate validity via Policy...")
                
                with self.db_session_factory() as db:
                    # 1. Policy(두뇌) 호출: 내부의 Validator가 하이브리드 임계값을 계산하여 판단함
                    new_cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(
                        db=db,
                        current_cert_data=self.publisher_connection_manager.cert_data
                    )
                    
                    # 2. 만약 Policy가 '새 인증서'를 반환했다면 (기존 데이터와 다를 경우)
                    if new_cert_data != self.publisher_connection_manager.cert_data:
                        logger.warning("🔄 New certificate acquired. Commanding Manager to rotate...")
                        
                        # 3. Manager에게 실제 교체 명령 하달
                        await self.publisher_connection_manager.rotate_certificate(new_cert_data)
                        logger.info("✅ MQTT Certificate rotation command completed.")
                    else:
                        logger.info("✅ Current certificate is still valid. No rotation needed.")

            except asyncio.CancelledError:
                logger.info("MQTT Rotation Monitor Loop is being cancelled...")
                break
            except Exception as e:
                logger.error(f"❌ Error in MQTT rotation monitor loop: {e}", exc_info=True)
                # 에러 발생 시 1분 후 다시 시도
                await asyncio.sleep(60)
                

    async def startup(self):
        """
        Publisher 클라이언트를 설정하고 시작합니다. (Non-blocking)
        """
        logger.info("MqttLifecycleOrchestrator starting up...")
        with self.db_session_factory() as db:
            try:
                # 1. 초기 인증서 획득
                logger.info("Setting up MQTT Publisher client...")
                logger.info("Acquiring certificate for MQTT publisher...")
                publisher_cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(
                    db=db, 
                    current_cert_data=None
                )
                
                # 2. Connection Manager 초기화
                logger.info("Initializing MqttConnectionManager for publisher...")
                self.publisher_connection_manager = MqttConnectionManager(
                    settings=self.settings,
                    client_id=self.settings.MQTT_CLIENT_ID
                )
                self.publisher_connection_manager.set_certificate_data(publisher_cert_data)
                
                # 3. Repository 등록
                logger.info("Initializing and registering CommandDispatchRepository...")
                command_dispatch_repo = CommandDispatchRepository(
                    settings=self.settings,
                    connection_manager=self.publisher_connection_manager
                )
                app_registry.command_dispatch_repository = command_dispatch_repo
                
                # 4. MQTT 연결 시작 (비동기 백그라운드 작업)
                # [참고] main.py에서 이 startup 자체를 create_task로 실행하므로 
                # 여기서의 sleep과 connect_task는 안전하게 비차단식으로 작동합니다.
                await asyncio.sleep(5)
                logger.info("Initiating MQTT connection in background task...")
                # [수정] 태스크를 인스턴스 변수에 저장하여 GC로부터 보호
                self._connect_task = asyncio.create_task(self.publisher_connection_manager.connect())
                
                # 5. 자율 운영을 위한 로테이션 감시 루프 시작
                self._rotation_monitor_task = asyncio.create_task(self._rotation_monitoring_loop())
                
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
        
        # 0. 연결 태스크가 진행 중이라면 취소
        if self._connect_task:
            self._connect_task.cancel()

        # 1. 감시 루프 태스크 취소
        if self._rotation_monitor_task:
            self._rotation_monitor_task.cancel()
            try:
                await self._rotation_monitor_task
            except asyncio.CancelledError:
                pass
            logger.info("MQTT Rotation Monitor Task cancelled.")
            
        # 2. MQTT 연결 해제
        if self.publisher_connection_manager:
            await self.publisher_connection_manager.disconnect()
            logger.info("MQTT Publisher client disconnected.")
        logger.info("MqttLifecycleOrchestrator shutdown completed.")

    def is_publisher_connected(self) -> bool:
        """
        Publisher용 MQTT 클라이언트가 현재 브로커에 연결되어 있는지 여부를 반환합니다.
        """
        return self.publisher_connection_manager.is_connected if self.publisher_connection_manager else False