import logging
import json
from typing import Callable, Optional, Dict
from sqlalchemy.orm import Session
import redis
from gmqtt import Client as MQTTClient

# Import the policy this router will use
from app.domains.action_authorization.policies.telemetry_ingestion.telemetry_ingestion_policy import telemetry_ingestion_policy

logger = logging.getLogger(__name__)

class MqttMessageRouter:
    """
    MQTT 메시지를 토픽에 따라 적절한 Policy 또는 핸들러로 라우팅하는 책임을 가집니다.
    """
    def __init__(self, db_session_factory: Callable[..., Session], redis_client: redis.Redis):
        self.db_session_factory = db_session_factory
        self.redis_client = redis_client

    async def handle_message(self, client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Dict):
        """
        gmqtt 클라이언트의 on_message 콜백으로 사용될 메서드입니다.
        """
        with self.db_session_factory() as db:
            try:
                logger.info(f"Routing message from topic: {topic}")
                
                try:
                    payload_dict = json.loads(payload.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logger.error(f"Failed to decode payload from topic {topic}")
                    return

                topic_parts = topic.split('/')

                if topic_parts[0] == 'telemetry':
                    # 기기(라즈베리파이) -> 서버: 텔레메트리 데이터 보고
                    self._handle_telemetry(db, topic_parts, payload_dict)
                elif topic_parts[0] == 'client' and topic_parts[1] == 'request_state':
                    # Flutter 앱 -> 서버: 앱이 서버에게 최신 상태를 요청
                    self._handle_state_request(client, topic_parts, payload_dict)
                # 'device/lwt/status/#' 토픽은 Flutter 앱 연결 상태용이며, 라즈베리파이 상태와 무관하므로 처리하지 않습니다.
                else:
                    logger.warning(f"No handler for topic: {topic}")

            except Exception as e:
                logger.error(f"Error in message routing for topic {topic}: {e}", exc_info=True)


    def _handle_telemetry(self, db: Session, topic_parts: list, payload: dict):
        if len(topic_parts) < 3:
            logger.warning(f"Invalid telemetry topic: {'/'.join(topic_parts)}")
            return
        device_uuid_str = topic_parts[2]
        
        is_valid, error_msg = telemetry_ingestion_policy.ingest(
            db=db,
            device_uuid_str=device_uuid_str,
            payload=payload
        )
        if not is_valid:
            logger.warning(f"Telemetry ingestion failed for device {device_uuid_str}: {error_msg}")
            db.rollback() # Explicitly rollback on policy failure
        else:
            db.commit() # Commit the transaction if ingestion policy succeeds

    def _handle_state_request(self, client: MQTTClient, topic_parts: list, payload: dict):
        """
        'client/request_state/#' 토픽의 메시지를 처리합니다.
        Redis에서 기기 상태를 가져와 Flutter 앱에게 다시 발행합니다.
        """
        if len(topic_parts) < 4:
            logger.warning(f"Invalid state request topic: {'/'.join(topic_parts)}")
            return
        user_email, device_uuid = topic_parts[2], topic_parts[3]
        state_key = f"device_state:{device_uuid}"
        try:
            cached_state = self.redis_client.hgetall(state_key)
            decoded_state = {k: v for k, v in cached_state.items()} if cached_state else {}
            response_payload = json.dumps(decoded_state)
            response_topic = f"client/state/{user_email}/{device_uuid}" # 서버 -> Flutter 앱: 상태 전파
            client.publish(response_topic, response_payload)
            logger.info(f"Sent state for {device_uuid} to {response_topic}. State: {response_payload}")
        except Exception as e:
            logger.error(f"Failed to handle state request for {device_uuid}: {e}", exc_info=True)
