import logging
import json
from typing import Dict
from gmqtt import Client as MQTTClient
import redis

# [중요] DB 저장 로직(Dispatcher) 대신, 실시간 서비스(RealtimeService)를 부릅니다.
from app.domains.services.realtime.services.realtime_device_service import RealtimeDeviceService

logger = logging.getLogger(__name__)

class MqttHandler:
    """
    [Application Layer]
    MQTT 메시지를 수신하여 Realtime 도메인 서비스로 연결(Wiring)합니다.
    DB 저장은 하지 않습니다. (그건 Webhook이 함)
    """
    def __init__(self, redis_client: redis.Redis):
        # 도메인 서비스(실무자) 조립
        self.realtime_service = RealtimeDeviceService(redis_client)

    async def handle_message(self, client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Dict):
        try:
            # 1. 메시지 파싱
            try:
                payload_str = payload.decode('utf-8')
                payload_dict = json.loads(payload_str)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return 

            topic_parts = topic.split('/')

            # 2. 라우팅 (Routing)
            
            # Case A: 텔레메트리 -> 실시간 서비스 (Redis 캐싱 & 전파)
            # 토픽 예: ares4/{uuid}/telemetry
            if len(topic_parts) == 3 and topic_parts[0] == 'ares4' and topic_parts[2] == 'telemetry':
                device_uuid = topic_parts[1]
                await self.realtime_service.process_telemetry(device_uuid, payload_dict)

            # Case B: 상태 요청 -> 실시간 서비스 (Redis 조회 & 응답)
            # 토픽 예: client/request_state/{email}/{uuid}
            elif topic_parts[0] == 'client' and topic_parts[1] == 'request_state':
                await self.realtime_service.handle_state_request(client, topic_parts)

        except Exception as e:
            logger.error(f"MQTT Handler Error: {e}")