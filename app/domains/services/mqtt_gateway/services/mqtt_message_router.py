import logging
import json
from typing import Callable, Dict
from sqlalchemy.orm import Session
import redis
from gmqtt import Client as MQTTClient

# [수정] 전문가를 직접 부르지 않고, 중앙 디스패처 제공자를 통합니다.
from app.domains.inter_domain.policies.ingestion.ingestion_dispatcher_provider import ingestion_dispatcher_provider

logger = logging.getLogger(__name__)

class MqttMessageRouter:
    """
    MQTT 메시지를 분석하여 중앙 디스패처로 전달하거나,
    실시간 상태 요청을 처리하는 역할을 수행합니다.
    """
    def __init__(self, db_session_factory: Callable[..., Session], redis_client: redis.Redis):
        self.db_session_factory = db_session_factory
        self.redis_client = redis_client

    async def handle_message(self, client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Dict):
        """gmqtt 클라이언트의 on_message 콜백"""
        with self.db_session_factory() as db:
            try:
                # 1. 페이로드 디코딩
                try:
                    payload_dict = json.loads(payload.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logger.error(f"ROUTER: Failed to decode payload from topic {topic}")
                    return
                
                # 2. 토픽 분석 및 분기
                topic_parts = topic.split('/')
                
                # 텔레메트리 데이터 (수집 경로)
                if topic_parts[0] == 'telemetry':
                    logger.info(f"ROUTER: Inbound telemetry dispatching for {topic}")
                    
                    # [핵심] 중앙 디스패처에게 모든 처리를 위임합니다.
                    is_valid, error_msg = ingestion_dispatcher_provider.dispatch(
                        db=db,
                        topic=topic,
                        payload=payload_dict
                    )
                    
                    if is_valid:
                        db.commit() # 처리가 성공하면 최종 커밋
                    else:
                        logger.warning(f"ROUTER: Ingestion failed: {error_msg}")
                        db.rollback()

                # Flutter 앱의 실시간 상태 요청 (제어 경로)
                elif topic_parts[0] == 'client' and topic_parts[1] == 'request_state':
                    self._handle_state_request(client, topic_parts, payload_dict)
                
                else:
                    logger.debug(f"ROUTER: No handler for topic: {topic}")

            except Exception as e:
                logger.error(f"ROUTER: Error in message routing for topic {topic}: {e}", exc_info=True)

    def _handle_state_request(self, client: MQTTClient, topic_parts: list, payload: dict):
        """기존 Redis 상태 조회 및 응답 로직 유지"""
        if len(topic_parts) < 4:
            logger.warning(f"ROUTER: Invalid state request topic: {'/'.join(topic_parts)}")
            return
            
        user_email, device_uuid = topic_parts[2], topic_parts[3]
        state_key = f"device_state:{device_uuid}"
        
        try:
            cached_state = self.redis_client.hgetall(state_key)
            response_payload = json.dumps(cached_state) if cached_state else "{}"
            response_topic = f"client/state/{user_email}/{device_uuid}"
            
            client.publish(response_topic, response_payload)
            logger.info(f"ROUTER: State published to {response_topic}")
        except Exception as e:
            logger.error(f"ROUTER: Failed to handle state request for {device_uuid}: {e}")