import logging
import sys
import os
import redis
import asyncio
import signal  # <-- 추가: 시스템 신호 처리

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import get_settings
from app.database import SessionLocal
from app.domains.services.mqtt_gateway.managers.mqtt_listener_manager import MqttListenerManager
from app.domains.application.mqtt_gateway.mqtt_handler import MqttHandler
from app.domains.inter_domain.policies.server_certificate_acquisition.server_certificate_acquisition_policy import server_certificate_acquisition_policy_provider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 전역에서 종료 이벤트를 관리합니다.
shutdown_event = asyncio.Event()

def signal_handler():
    """시스템 종료 신호(SIGINT, SIGTERM)를 받으면 이벤트를 세팅합니다."""
    logger.info("Shutdown signal received. Initiating graceful shutdown...")
    shutdown_event.set()

async def rotation_monitoring_loop(manager, settings):
    """
    [Ares Aegis] 주기적으로 인증서 상태를 체크하고 로테이션을 지휘합니다.
    """
    logger.info("📡 Listener Certificate Rotation Monitor started.")
    while not shutdown_event.is_set():
        try:
            # 1시간(3600초)마다 체크
            await asyncio.sleep(3600)
            
            with SessionLocal() as db:
                logger.info("🔍 Checking listener certificate validity...")
                new_cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(
                    db=db,
                    current_cert_data=manager.cert_data
                )
                
                # 새 인증서가 발급되었다면 교체 명령
                if new_cert_data != manager.cert_data:
                    logger.warning("🔄 New certificate acquired. Rotating listener connection...")
                    await manager.rotate_certificate(new_cert_data)
                    db.commit()
                else:
                    logger.info("✅ Certificate is still valid.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"❌ Error in rotation monitor: {e}")
            await asyncio.sleep(60)

async def main():
    logger.info("Starting MQTT listener application with survival features...")
    
    manager = None
    settings = get_settings()

    # 1. 시그널 핸들러 등록 (Windows 환경 고려하여 예외 처리)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows에서는 add_signal_handler가 지원되지 않을 수 있음
            pass

    try:
        # 2. Redis 및 핸들러 초기화
        redis_client = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT,
            db=settings.REDIS_DB, decode_responses=True
        )
        mqtt_handler = MqttHandler(redis_client=redis_client)
        manager = MqttListenerManager(settings=settings, client_id=settings.MQTT_LISTENER_CLIENT_ID)

        # 3. 초기 인증서 획득
        logger.info("Acquiring initial certificate...")
        with SessionLocal() as db:
            cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(
                db=db, current_cert_data=None
            )
            db.commit()
        
        manager.set_certificate_data(cert_data)

        # 4. MQTT 연결 (비차단)
        await manager.connect(on_message_callback=mqtt_handler.handle_message)
        
        # 5. 로테이션 감시 루프를 백그라운드에서 실행
        rotation_task = asyncio.create_task(rotation_monitoring_loop(manager, settings))

        logger.info("MQTT listener is active. Watching for messages and certificate health...")
        
        # 종료 신호가 올 때까지 대기
        await shutdown_event.wait()
        
        # 6. 정리 작업
        rotation_task.cancel()
        await asyncio.gather(rotation_task, return_exceptions=True)

    except Exception as e:
        logger.error(f"Critical error in listener: {e}", exc_info=True)
    finally:
        if manager:
            await manager.disconnect()
        logger.info("MQTT listener application has shut down safely.")

if __name__ == "__main__":
    asyncio.run(main())