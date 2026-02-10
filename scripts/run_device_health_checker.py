import logging
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.config import settings
from app.core.redis_client import get_redis_client # [개선] 공통 모듈 사용
from app.models.objects.device import DeviceStatusEnum

# --- 인터도메인 제공자(전문가) 임포트 ---
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.device_log.device_log_command_provider import device_log_command_provider
from app.domains.inter_domain.mqtt_gateway.mqtt_command_provider import mqtt_command_provider
from app.domains.inter_domain.policies.server_certificate_acquisition.server_certificate_acquisition_policy import server_certificate_acquisition_policy

logger = logging.getLogger(__name__)

async def check_device_health():
    """Redis 상태를 확인하여 타임아웃 기기를 판별하고 조치합니다."""
    redis_client = get_redis_client()
    db: Session = SessionLocal()
    
    try:
        # device_state:* 패턴의 모든 키를 가져옴
        for key in redis_client.scan_iter("device_state:*"):
            # [수정] Redis 키가 bytes 타입으로 올 경우를 대비해 문자열로 변환합니다.
            if isinstance(key, bytes):
                key = key.decode('utf-8')
                
            device_uuid_str = key.split(':')[1]
            cached_state = redis_client.hgetall(key)
            
            # [수정] Redis 필드값들도 문자열로 변환하여 에러를 방지합니다.
            state = {
                (k.decode('utf-8') if isinstance(k, bytes) else k): 
                (v.decode('utf-8') if isinstance(v, bytes) else v) 
                for k, v in cached_state.items()
            }
            
            # ONLINE 상태인 기기만 검사
            if state.get("device_status") == DeviceStatusEnum.ONLINE.value:
                last_seen_at_raw = state.get("last_seen_at")
                if not last_seen_at_raw:
                    continue
                    
                last_seen_at = datetime.fromisoformat(last_seen_at_raw).replace(tzinfo=timezone.utc)
                
                # 설정된 타임아웃 시간을 초과했는지 확인
                if (datetime.now(timezone.utc) - last_seen_at) > timedelta(seconds=settings.DEVICE_TIMEOUT_SECONDS):
                    logger.warning(f"🚨 Device {device_uuid_str} timed out.")
                    
                    # 1. Redis 상태 업데이트
                    redis_client.hset(key, "device_status", DeviceStatusEnum.TIMEOUT.value)
                    
                    # 2. DB 상태 업데이트 및 로그 기록 (Provider 활용)
                    try:
                        # [핵심 수정] UUID 형식을 엄격하게 검사합니다. 
                        # 형식이 틀리면 ValueError가 발생하며, 해당 키는 처리하지 않고 넘어갑니다.
                        device_uuid = uuid.UUID(device_uuid_str)
                        
                        db_device = device_management_query_provider.get_device_by_uuid(db, current_uuid=device_uuid)
                        if db_device and db_device.status != DeviceStatusEnum.TIMEOUT:
                            db_device.status = DeviceStatusEnum.TIMEOUT
                            device_log_command_provider.create_device_log(
                                db=db, device_id=db_device.id, log_level="WARNING",
                                description=f"Device timed out. Last seen at {last_seen_at.isoformat()}."
                            )
                            db.commit()

                        # 3. [핵심] 헬스체커가 직접 MQTT 명령 발행 (HTTP 대신 Provider 호출)
                        if user_email := state.get("user_email"):
                            mqtt_command_provider.publish_command(
                                db=db,
                                topic=f"users/{user_email}/devices/{device_uuid_str}/status",
                                command={"status": DeviceStatusEnum.TIMEOUT.value}
                            )
                    except ValueError:
                        # UUID 형식이 아닌 잘못된 키에 대한 경고 로그
                        logger.error(f"❌ Invalid UUID format found in Redis key: '{device_uuid_str}'. Skipping this entry.")
                        continue
                            
    except Exception as e:
        logger.error(f"Health Checker Loop Error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

async def main():
    logger.info("🚀 Ares4 Device Health Checker Running...")
    db: Session = SessionLocal()
    
    try:
        # 1. 인증서 획득(Policy 호출)
        logger.info("🔑 Acquiring MQTT certificate via Policy...")
        
        # 동기 함수가 루프를 차단하지 않도록 별도 쓰레드에서 실행
        loop = asyncio.get_running_loop()
        new_cert_data = await loop.run_in_executor(
            None,
            lambda: server_certificate_acquisition_policy.acquire_valid_server_certificate(
                db=db,
                current_cert_data=None
            )
        )
        
        # 2. Connection Manager에 인증서 데이터 주입
        mqtt_command_provider._connection_manager.set_certificate_data(new_cert_data)
        
        # 3. 연결 수립
        await mqtt_command_provider._connection_manager.connect()
        logger.info("✅ MQTT Connection established for health checker.")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return
    finally:
        db.close()

    while True:
        await check_device_health()
        await asyncio.sleep(settings.DEVICE_HEALTH_CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())