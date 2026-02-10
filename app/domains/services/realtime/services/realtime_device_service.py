import logging
import json
import redis
from gmqtt import Client as MQTTClient

logger = logging.getLogger(__name__)

class RealtimeDeviceService:
    """
    [Domain Layer]
    실시간 데이터 처리 비즈니스 로직 (Redis 저장, 전파 등)
    """
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def process_telemetry(self, device_uuid: str, payload: dict):
        # 1. Redis 캐싱 (Hot Path)
        redis_key = f"device_state:{device_uuid}"
        
        # decode_responses=True 덕분에 그냥 넣으면 됩니다.
        self.redis_client.hset(redis_key, mapping=payload)
        logger.info(f"🔥 Cached telemetry for {device_uuid}")
        
        # 2. (추후 추가) WebSocket으로 프론트엔드에 전송
        # await websocket_manager.broadcast(...)

    async def handle_state_request(self, client: MQTTClient, topic_parts: list):
        # Redis 조회 및 응답 로직
        user_email, device_uuid = topic_parts[2], topic_parts[3]
        redis_key = f"device_state:{device_uuid}"
        
        try:
            # [수정] decode_responses=True이므로, 리턴값은 이미 dict[str, str]입니다.
            # 복잡한 decode() 로직 삭제!
            data = self.redis_client.hgetall(redis_key)
            
            # 데이터가 없을 경우 빈 dict 처리
            if not data:
                data = {}

            resp_topic = f"client/state/{user_email}/{device_uuid}"
            client.publish(resp_topic, json.dumps(data))
            logger.info(f"📤 Sent state snapshot to {resp_topic}")
            
        except Exception as e:
            logger.error(f"Failed to handle state request: {e}")